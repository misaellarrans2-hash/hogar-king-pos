from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.decorators import roles_requeridos
from app.extensions import db
from app.models import Factura, FacturaItem, Producto, Rol, Stock

ventas_bp = Blueprint("ventas", __name__, url_prefix="/ventas")

CARRITO_SESSION_KEY = "carrito"


def _carrito():
    return session.setdefault(CARRITO_SESSION_KEY, [])


def _guardar_carrito(carrito):
    session[CARRITO_SESSION_KEY] = carrito
    session.modified = True


def _lineas_carrito():
    """Convierte el carrito (solo ids/cantidades en la sesion) en lineas
    con los datos del producto y el stock disponible, para mostrarlas."""
    lineas = []
    subtotal = Decimal("0")
    for entrada in _carrito():
        producto = Producto.query.get(entrada["producto_id"])
        if producto is None:
            continue
        stock = producto.stock_en(current_user.sede_id)
        cantidad = entrada["cantidad"]
        subtotal_linea = producto.precio_venta * cantidad
        subtotal += subtotal_linea
        lineas.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "precio_unitario": producto.precio_venta,
                "subtotal_linea": subtotal_linea,
                "stock_disponible": stock.cantidad if stock else 0,
            }
        )
    return lineas, subtotal


@ventas_bp.route("/nueva")
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def nueva():
    lineas, subtotal = _lineas_carrito()
    return render_template(
        "ventas/nueva.html",
        lineas=lineas,
        subtotal=subtotal,
        formas_pago=Factura.FORMAS_PAGO,
    )


@ventas_bp.route("/carrito/agregar", methods=["POST"])
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def agregar_al_carrito():
    codigo = request.form.get("codigo", "").strip()
    cantidad = request.form.get("cantidad", type=int) or 1

    producto = Producto.query.filter_by(codigo=codigo, activo=True).first()
    if producto is None:
        flash(f"No existe ningun producto con el codigo {codigo}.", "danger")
        return redirect(url_for("ventas.nueva"))

    stock = producto.stock_en(current_user.sede_id)
    disponible = stock.cantidad if stock else 0

    carrito = _carrito()
    ya_en_carrito = next((c for c in carrito if c["producto_id"] == producto.id), None)
    cantidad_actual = ya_en_carrito["cantidad"] if ya_en_carrito else 0

    if cantidad_actual + cantidad > disponible:
        flash(f"No hay suficiente stock de {producto.nombre} (disponible: {disponible}).", "danger")
        return redirect(url_for("ventas.nueva"))

    if ya_en_carrito:
        ya_en_carrito["cantidad"] += cantidad
    else:
        carrito.append({"producto_id": producto.id, "cantidad": cantidad})

    _guardar_carrito(carrito)
    return redirect(url_for("ventas.nueva"))


@ventas_bp.route("/carrito/quitar/<int:producto_id>", methods=["POST"])
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def quitar_del_carrito(producto_id):
    carrito = [c for c in _carrito() if c["producto_id"] != producto_id]
    _guardar_carrito(carrito)
    return redirect(url_for("ventas.nueva"))


@ventas_bp.route("/carrito/vaciar", methods=["POST"])
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def vaciar_carrito():
    _guardar_carrito([])
    return redirect(url_for("ventas.nueva"))


@ventas_bp.route("/finalizar", methods=["POST"])
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def finalizar():
    lineas, subtotal = _lineas_carrito()

    if not lineas:
        flash("El carrito esta vacio.", "danger")
        return redirect(url_for("ventas.nueva"))

    forma_pago = request.form.get("forma_pago")
    if forma_pago not in Factura.FORMAS_PAGO:
        flash("Selecciona una forma de pago valida.", "danger")
        return redirect(url_for("ventas.nueva"))

    cliente_referencia = request.form.get("cliente_referencia", "").strip() or None
    descuento_pct = _a_decimal(request.form.get("descuento_pct")) or Decimal("0")
    if descuento_pct < 0 or descuento_pct > 100:
        descuento_pct = Decimal("0")

    # Revalidar stock justo antes de vender, por si cambio desde que se armo el carrito.
    for linea in lineas:
        stock = linea["producto"].stock_en(current_user.sede_id)
        if stock is None or stock.cantidad < linea["cantidad"]:
            flash(f"Ya no hay suficiente stock de {linea['producto'].nombre}.", "danger")
            return redirect(url_for("ventas.nueva"))

    descuento_total = (subtotal * descuento_pct / Decimal("100")).quantize(Decimal("0.01"))
    total = subtotal - descuento_total

    ultimo_numero = (
        db.session.query(db.func.max(Factura.numero)).filter_by(sede_id=current_user.sede_id).scalar()
    )
    numero = (ultimo_numero or 0) + 1

    factura = Factura(
        numero=numero,
        sede_id=current_user.sede_id,
        usuario_id=current_user.id,
        cliente_referencia=cliente_referencia,
        subtotal=subtotal,
        descuento_total=descuento_total,
        total=total,
        forma_pago=forma_pago,
    )
    db.session.add(factura)
    db.session.flush()

    for linea in lineas:
        db.session.add(
            FacturaItem(
                factura_id=factura.id,
                producto_id=linea["producto"].id,
                cantidad=linea["cantidad"],
                precio_unitario=linea["precio_unitario"],
                subtotal_linea=linea["subtotal_linea"],
            )
        )
        stock = linea["producto"].stock_en(current_user.sede_id)
        stock.cantidad -= linea["cantidad"]

    db.session.commit()
    _guardar_carrito([])

    return redirect(url_for("ventas.ver_factura", factura_id=factura.id))


@ventas_bp.route("/factura/<int:factura_id>")
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def ver_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    if not current_user.ve_todas_las_sedes() and factura.sede_id != current_user.sede_id:
        return redirect(url_for("ventas.nueva"))
    return render_template("ventas/factura.html", factura=factura)


@ventas_bp.route("/factura/<int:factura_id>/anular", methods=["POST"])
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def anular_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)

    if not current_user.ve_todas_las_sedes() and factura.sede_id != current_user.sede_id:
        flash("No puedes anular facturas de otra sede.", "danger")
        return redirect(url_for("ventas.historial"))

    if current_user.tiene_rol(Rol.CAJERO) and factura.usuario_id != current_user.id:
        flash("Solo puedes anular tus propias facturas.", "danger")
        return redirect(url_for("ventas.historial"))

    if factura.estado == Factura.ANULADA:
        flash("Esta factura ya estaba anulada.", "warning")
        return redirect(url_for("ventas.ver_factura", factura_id=factura.id))

    for item in factura.items:
        stock = item.producto.stock_en(factura.sede_id)
        if stock:
            stock.cantidad += item.cantidad

    factura.estado = Factura.ANULADA
    factura.anulada_por_id = current_user.id
    factura.anulada_en = datetime.utcnow()
    db.session.commit()

    flash(f"Factura #{factura.numero} anulada. El stock fue devuelto.", "success")
    return redirect(url_for("ventas.ver_factura", factura_id=factura.id))


@ventas_bp.route("/historial")
@login_required
@roles_requeridos(Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.CAJERO)
def historial():
    sede_id = current_user.sede_id if not current_user.ve_todas_las_sedes() else request.args.get("sede_id", type=int)
    query = Factura.query
    if sede_id:
        query = query.filter_by(sede_id=sede_id)
    facturas = query.order_by(Factura.creado_en.desc()).limit(100).all()
    return render_template("ventas/historial.html", facturas=facturas, sedes_visibles=current_user.sedes_visibles())


def _a_decimal(valor):
    if valor is None or valor == "":
        return None
    try:
        return Decimal(valor)
    except InvalidOperation:
        return None
