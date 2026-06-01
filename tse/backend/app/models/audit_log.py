# Tabla audit_logs
from app.extensions import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger,primary_key=True)
    usuario_id = db.Column(db.Integer,db.ForeignKey('usuarios.id'))
    eleccion_id = db.Column(db.Integer,db.ForeignKey('elecciones.id'))
    accion = db.Column(db.String(50),nullable=False)
    descripcion = db.Column(db.Text)
    ip_hash = db.Column(db.String(64))
    hash_integridad = db.Column(db.String(64),nullable=False)
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

    usuario = db.relationship("Usuario",backref="logs")
    eleccion = db.relationship("Eleccion",backref="logs")