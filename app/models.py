from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class Sede(db.Model):
    __tablename__ = "sedes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    direccion = db.Column(db.String(200))

    usuarios = db.relationship("Usuario", back_populates="sede")

    def __repr__(self):
        return f"<Sede {self.nombre}>"


class Rol(db.Model):
    __tablename__ = "roles"

    SUPERADMIN = "SUPERADMIN"
    ADMINSEDE = "ADMINSEDE"
    CAJERO = "CAJERO"
    BODEGUERO = "BODEGUERO"
    ASESOR = "ASESOR"

    TODOS = (SUPERADMIN, ADMINSEDE, CAJERO, BODEGUERO, ASESOR)

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))

    usuarios = db.relationship("Usuario", back_populates="rol")

    def __repr__(self):
        return f"<Rol {self.nombre}>"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    # sede_id es NULL para SUPERADMIN, que ve las dos sedes.
    sede_id = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=True)

    rol = db.relationship("Rol", back_populates="usuarios")
    sede = db.relationship("Sede", back_populates="usuarios")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def tiene_rol(self, *nombres_rol):
        return self.rol.nombre in nombres_rol

    def ve_todas_las_sedes(self):
        return self.rol.nombre == Rol.SUPERADMIN

    def puede_ver_costos(self):
        # Solo el dueño ve costos y ganancias (regla de negocio original).
        return self.rol.nombre == Rol.SUPERADMIN

    def puede_ver_precios(self):
        return self.rol.nombre in (Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.ASESOR)

    def puede_editar_productos(self):
        return self.rol.nombre in (Rol.SUPERADMIN, Rol.ADMINSEDE)

    def puede_registrar_movimientos(self):
        return self.rol.nombre in (Rol.SUPERADMIN, Rol.ADMINSEDE, Rol.BODEGUERO)

    def sedes_visibles(self):
        """Sedes cuyo inventario puede consultar este usuario."""
        if self.ve_todas_las_sedes():
            return Sede.query.order_by(Sede.nombre).all()
        return [self.sede] if self.sede else []

    def __repr__(self):
        return f"<Usuario {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(300))
    precio_venta = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    costo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    stocks = db.relationship("Stock", back_populates="producto", cascade="all, delete-orphan")
    movimientos = db.relationship("MovimientoInventario", back_populates="producto")
    historial_precios = db.relationship("HistorialPrecio", back_populates="producto")

    def stock_en(self, sede_id):
        for stock in self.stocks:
            if stock.sede_id == sede_id:
                return stock
        return None

    def __repr__(self):
        return f"<Producto {self.codigo} {self.nombre}>"


class Stock(db.Model):
    __tablename__ = "stocks"
    __table_args__ = (db.UniqueConstraint("producto_id", "sede_id", name="uq_stock_producto_sede"),)

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    sede_id = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0)

    producto = db.relationship("Producto", back_populates="stocks")
    sede = db.relationship("Sede")

    @property
    def stock_bajo(self):
        return self.cantidad <= self.stock_minimo

    def __repr__(self):
        return f"<Stock producto={self.producto_id} sede={self.sede_id} cantidad={self.cantidad}>"


class MovimientoInventario(db.Model):
    __tablename__ = "movimientos_inventario"

    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    TIPOS = (ENTRADA, SALIDA)

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    sede_id = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship("Producto", back_populates="movimientos")
    sede = db.relationship("Sede")
    usuario = db.relationship("Usuario")

    def __repr__(self):
        return f"<Movimiento {self.tipo} producto={self.producto_id} cantidad={self.cantidad}>"


class HistorialPrecio(db.Model):
    __tablename__ = "historial_precios"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    precio_anterior = db.Column(db.Numeric(12, 2), nullable=False)
    precio_nuevo = db.Column(db.Numeric(12, 2), nullable=False)
    costo_anterior = db.Column(db.Numeric(12, 2))
    costo_nuevo = db.Column(db.Numeric(12, 2))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship("Producto", back_populates="historial_precios")
    usuario = db.relationship("Usuario")

    def __repr__(self):
        return f"<HistorialPrecio producto={self.producto_id} {self.precio_anterior}->{self.precio_nuevo}>"
