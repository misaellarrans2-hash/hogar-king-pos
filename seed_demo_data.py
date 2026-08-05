"""Crea las tablas de la base de datos y carga datos de ejemplo
(sedes, roles y usuarios demo) para poder mostrar el sistema.

Uso:
    python seed_demo_data.py
"""

from app import create_app
from app.extensions import db
from app.models import Producto, Rol, Sede, Stock, Usuario

ROLES = [
    (Rol.SUPERADMIN, "Dueño. Control total de las 2 sedes, ve costos y ganancias."),
    (Rol.ADMINSEDE, "Administrador de una sede. Ve todo de su sede, no ve costos ni la otra sede."),
    (Rol.CAJERO, "Vende, cobra y hace el cierre de su caja."),
    (Rol.BODEGUERO, "Maneja inventario, entradas y traslados de su sede."),
    (Rol.ASESOR, "Consulta precios y stock de su sede para atender clientes."),
]

SEDES = [
    ("Sede Centro", "Centro, Santa Marta"),
    ("Sede La Lucha", "La Lucha, Santa Marta"),
]

# (username, nombre_completo, rol, nombre_sede o None para SUPERADMIN)
USUARIOS_DEMO = [
    ("superadmin", "Dueño Hogar King", Rol.SUPERADMIN, None),
    ("admin_centro", "Admin Sede Centro", Rol.ADMINSEDE, "Sede Centro"),
    ("admin_lalucha", "Admin Sede La Lucha", Rol.ADMINSEDE, "Sede La Lucha"),
    ("cajero_centro", "Cajero Sede Centro", Rol.CAJERO, "Sede Centro"),
    ("cajero_lalucha", "Cajero Sede La Lucha", Rol.CAJERO, "Sede La Lucha"),
    ("bodeguero_centro", "Bodeguero Sede Centro", Rol.BODEGUERO, "Sede Centro"),
    ("bodeguero_lalucha", "Bodeguero Sede La Lucha", Rol.BODEGUERO, "Sede La Lucha"),
    ("asesor_centro", "Asesor Sede Centro", Rol.ASESOR, "Sede Centro"),
    ("asesor_lalucha", "Asesor Sede La Lucha", Rol.ASESOR, "Sede La Lucha"),
]


# (codigo, nombre, precio_venta, costo, {nombre_sede: (cantidad, stock_minimo)})
PRODUCTOS_DEMO = [
    ("7701234560012", "Resma de papel carta x500", 18000, 12000,
     {"Sede Centro": (40, 10), "Sede La Lucha": (5, 10)}),
    ("7701234560029", "Caja de lapices x12", 9500, 6000,
     {"Sede Centro": (25, 5), "Sede La Lucha": (30, 5)}),
    ("7701234560036", "Cuaderno cosido 100 hojas", 6500, 4000,
     {"Sede Centro": (60, 15), "Sede La Lucha": (18, 15)}),
    ("7701234560043", "Televisor 32 pulgadas Smart", 950000, 720000,
     {"Sede Centro": (3, 1)}),  # solo hay en Sede Centro, a proposito
    ("7701234560050", "Juego de sabanas doble", 85000, 55000,
     {"Sede La Lucha": (12, 3)}),  # solo hay en Sede La Lucha, a proposito
]


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        sedes_por_nombre = {}
        for nombre, direccion in SEDES:
            sede = Sede.query.filter_by(nombre=nombre).first()
            if sede is None:
                sede = Sede(nombre=nombre, direccion=direccion)
                db.session.add(sede)
            sedes_por_nombre[nombre] = sede

        roles_por_nombre = {}
        for nombre, descripcion in ROLES:
            rol = Rol.query.filter_by(nombre=nombre).first()
            if rol is None:
                rol = Rol(nombre=nombre, descripcion=descripcion)
                db.session.add(rol)
            roles_por_nombre[nombre] = rol

        db.session.flush()

        for username, nombre_completo, nombre_rol, nombre_sede in USUARIOS_DEMO:
            if Usuario.query.filter_by(username=username).first():
                continue
            usuario = Usuario(
                username=username,
                nombre_completo=nombre_completo,
                rol=roles_por_nombre[nombre_rol],
                sede=sedes_por_nombre[nombre_sede] if nombre_sede else None,
            )
            usuario.set_password(username)  # demo: la contraseña es igual al usuario
            db.session.add(usuario)

        for codigo, nombre, precio_venta, costo, stock_por_sede in PRODUCTOS_DEMO:
            producto = Producto.query.filter_by(codigo=codigo).first()
            if producto is None:
                producto = Producto(codigo=codigo, nombre=nombre, precio_venta=precio_venta, costo=costo)
                db.session.add(producto)
                db.session.flush()

            for nombre_sede, (cantidad, stock_minimo) in stock_por_sede.items():
                sede = sedes_por_nombre[nombre_sede]
                if producto.stock_en(sede.id) is None:
                    db.session.add(
                        Stock(producto_id=producto.id, sede_id=sede.id, cantidad=cantidad, stock_minimo=stock_minimo)
                    )

        db.session.commit()

        print("Datos de ejemplo cargados.")
        print("Usuarios demo (la contraseña es igual al usuario):")
        for username, _, rol, sede in USUARIOS_DEMO:
            extra = f", {sede}" if sede else ""
            print(f"  - {username}  ({rol}{extra})")


if __name__ == "__main__":
    seed()
