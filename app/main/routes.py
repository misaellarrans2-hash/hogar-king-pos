from flask import Blueprint, render_template
from flask_login import current_user, login_required

main_bp = Blueprint("main", __name__)

# Vista previa de los modulos futuros que cada rol podra usar.
# Cada modulo se activa en un PR posterior; por ahora solo se muestra
# como referencia de los permisos ya definidos por rol.
MODULOS_POR_ROL = {
    "SUPERADMIN": [
        "Ventas y Caja",
        "Inventario y Bodega",
        "Traslados entre Sedes",
        "Clientes y Cotizaciones",
        "Reportes y Administracion (ambas sedes, costos y ganancias)",
    ],
    "ADMINSEDE": [
        "Ventas y Caja",
        "Inventario y Bodega de su sede",
        "Traslados entre Sedes",
        "Clientes y Cotizaciones",
        "Reportes de su sede",
    ],
    "CAJERO": [
        "Ventas y Caja",
        "Cierre de caja y arqueo",
    ],
    "BODEGUERO": [
        "Inventario y Bodega de su sede (desde PC o celular)",
        "Traslados entre Sedes",
    ],
    "ASESOR": [
        "Consulta de precios y stock de su sede",
        "Cotizaciones",
    ],
}


@main_bp.route("/")
@login_required
def dashboard():
    modulos = MODULOS_POR_ROL.get(current_user.rol.nombre, [])
    return render_template("main/dashboard.html", modulos=modulos)
