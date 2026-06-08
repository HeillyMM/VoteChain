# Tabla elecciones
from app.extensions import db
from datetime import datetime

class Eleccion(db.Model):
    __tablename__ = "elecciones"

    id = db.Column(db.Integer,primary_key=True)
    codigo = db.Column(db.String(30),nullable=False,unique=True)
    titulo = db.Column(db.String(200),nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Enum('PRESIDENCIAL','MUNICIPAL','DEPARTAMENTAL','REFERENDUM','ASAMBLEA'),nullable=False)
    estado = db.Column(db.Enum('CONFIGURACION','ACTIVA','SUSPENDIDA','CERRADA'),nullable=False,default='CONFIGURACION')
    fecha_inicio = db.Column(db.DateTime,nullable=False)
    fecha_fin = db.Column(db.DateTime)
    clave_publica_pem = db.Column(db.Text)
    clave_privada_pem = db.Column(db.Text)
    created_by = db.Column(db.Integer,db.ForeignKey('usuarios.id',ondelete='SET NULL'))
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)

    creador = db.relationship("Usuario",backref="elecciones_creadas")
    recintos = db.relationship("Recinto",secondary="recintos_elecciones",back_populates="elecciones")

class RecintoEleccion(db.Model):
    __tablename__ = "recintos_elecciones"

    recinto_id = db.Column(db.Integer,db.ForeignKey("recintos.id"),primary_key=True)
    eleccion_id = db.Column(db.Integer,db.ForeignKey("elecciones.id"),primary_key=True)