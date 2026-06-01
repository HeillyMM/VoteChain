# Tabla conteos
from app.extensions import db
from datetime import datetime

class Conteo(db.Model):
    __tablename__ = "conteos"

    __table_args__ = (
    db.UniqueConstraint(
        'eleccion_id',
        'candidato_id',
        'tipo',
        name='uq_conteo'
    ),
    )

    id = db.Column(db.Integer,primary_key=True)
    eleccion_id = db.Column(db.Integer,db.ForeignKey('elecciones.id',ondelete='CASCADE'),nullable=False)
    candidato_id = db.Column(db.Integer,db.ForeignKey('candidatos.id',ondelete='CASCADE'))
    tipo = db.Column(db.Enum('VALIDO','BLANCO','NULO'), nullable=False)
    total_votos = db.Column(db.Integer,nullable=False,default=0)
    updated_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)

    eleccion = db.relationship("Eleccion",backref="conteos")
    candidato = db.relationship("Candidato",backref="conteos")