# Tabla candidatos
from app.extensions import db
from datetime import datetime

class Candidato(db.Model):
    __tablename__ = "candidatos"

    __table_args__ = (
    db.UniqueConstraint(
        'eleccion_id',
        'numero_lista',
        name='uq_candidato_lista'
    ),
    )
    
    id = db.Column(db.Integer,primary_key=True)
    eleccion_id = db.Column(db.Integer,db.ForeignKey('elecciones.id'),nullable=False)
    numero_lista = db.Column(db.Integer,nullable=False)
    sigla_partido = db.Column(db.String(20),nullable=False)
    nombre_partido = db.Column(db.String(150))
    nombres = db.Column(db.String(100),nullable=False)
    apellido_paterno = db.Column(db.String(80),nullable=False)
    apellido_materno = db.Column(db.String(80))
    formula_nombres = db.Column(db.String(100))
    formula_apellido_paterno = db.Column(db.String(80))
    logo_partido = db.Column(db.String(200))
    foto_candidato = db.Column(db.String(200))
    color_partido = db.Column(db.String(7))
    propuesta_breve = db.Column(db.Text)
    activo = db.Column(db.Boolean,nullable=False,default=1)
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

    eleccion = db.relationship("Eleccion",backref="candidatos")