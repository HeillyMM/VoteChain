# Tablas recintos y kiocos
from app.extensions import db

class Recinto(db.Model):
    __tablename__ = "recintos"

    id = db.Column(db.Integer,primary_key=True)
    codigo = db.Column(db.String(20),nullable=False,unique=True)
    nombre = db.Column(db.String(150),nullable=False)
    direccion = db.Column(db.String(200))
    municipio = db.Column(db.String(80),nullable=False)
    departamento_id = db.Column(db.Integer,db.ForeignKey('departamentos.id'),nullable=False)
    total_mesas = db.Column(db.Integer,nullable=False,default=1)
    activo = db.Column(db.Boolean,nullable=False,default=1)

class Kiosco(db.Model):
    __tablename__ = "kioscos"

    __table_args__ = (
    db.UniqueConstraint(
        'recinto_id',
        'nombre',
        name='uq_kiosco_recinto'
    ),
    )

    id = db.Column(db.Integer,primary_key=True)
    recinto_id = db.Column(db.Integer,db.ForeignKey('recintos.id'),nullable=False)
    nombre = db.Column(db.String(50),nullable=False)
    ip_local = db.Column(db.String(15))
    activo = db.Column(db.Boolean,nullable=False,default=1)
    ultimo_uso = db.Column(db.DateTime)

    recinto = db.relationship("Recinto",backref="kioscos")

class Departamento(db.Model):
    __tablename__ = "departamentos"

    id = db.Column(db.Integer,primary_key=True)
    nombre = db.Column(db.String(50),nullable=False,unique=True)

    recintos = db.relationship("Recinto",backref="departamento",lazy=True)