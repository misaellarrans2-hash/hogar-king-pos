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
        return self.rol.nombre in (Rol.SUPERADMIN, Rol.ADMINSEDE)

    def __repr__(self):
        return f"<Usuario {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))
