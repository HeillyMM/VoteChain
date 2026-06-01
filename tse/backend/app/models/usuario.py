# Tablas usuarios y roles
from app.extensions import db
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer,primary_key=True)
    ci = db.Column(db.String(12),nullable=False,unique=True)
    nombres = db.Column(db.String(100),nullable=False)
    apellidos = db.Column(db.String(160),nullable=False)
    email = db.Column(db.String(120),nullable=False,unique=True)
    password_hash = db.Column(db.String(255),nullable=False)
    rol_id = db.Column(db.Integer,db.ForeignKey('roles.id'),nullable=False)
    activo = db.Column(db.Boolean,nullable=False,default=1)
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)

class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer,primary_key=True)
    nombre = db.Column(db.String(30),nullable=False,unique=True)
    descripcion = db.Column(db.Text)

    usuarios = db.relationship("Usuario",backref="rol",lazy=True)