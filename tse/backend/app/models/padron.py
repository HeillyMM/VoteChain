# Tablas padron electoral y sesiones kiosco
from app.extensions import db
from datetime import datetime

class PadronElectoral(db.Model):
    __tablename__ = "padron_electoral"
    __table_args__ = (db.UniqueConstraint('ci', 'eleccion_id', name='uq_ci_eleccion'),)

    id = db.Column(db.Integer,primary_key=True)
    ci = db.Column(db.String(12),nullable=False)
    complemento = db.Column(db.String(4))
    nombres = db.Column(db.String(100),nullable=False)
    apellido_paterno = db.Column(db.String(80),nullable=False)
    apellido_materno = db.Column(db.String(80))
    fecha_nacimiento = db.Column(db.Date,nullable=False)
    sexo = db.Column(db.Enum('M','F'),nullable=False)
    recinto_id = db.Column(db.Integer,db.ForeignKey('recintos.id'))
    mesa_numero = db.Column(db.Integer)
    habilitado = db.Column(db.Boolean,nullable=False,default=1)
    motivo_inhabilitacion = db.Column(db.String(200))
    ya_voto = db.Column(db.Boolean,nullable=False,default=0)
    hora_voto = db.Column(db.DateTime)
    habilitado_por = db.Column(db.Integer,db.ForeignKey('usuarios.id'))
    eleccion_id = db.Column(db.Integer,db.ForeignKey('elecciones.id'),nullable=False)
    departamento_id = db.Column(db.Integer,db.ForeignKey('departamentos.id'),nullable=False)
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)

    #relacion eleccion
    eleccion = db.relationship("Eleccion",backref="padrones")
    #relacion departamento
    departamento = db.relationship("Departamento",backref="padrones")
    #relacion recinto_id
    recinto = db.relationship("Recinto",backref="padrones")
    #relacion habilitado_por
    habilitador = db.relationship("Usuario",backref="padrones")

class SesionKiosco(db.Model):
    __tablename__ = "sesiones_kiosco"

    id = db.Column(db.Integer,primary_key=True)
    operador_id = db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)
    padron_id = db.Column(db.Integer,db.ForeignKey('padron_electoral.id'),nullable=False)
    kiosco_id = db.Column(db.Integer,db.ForeignKey('kioscos.id'),nullable=False)
    token_hash = db.Column(db.String(64),nullable=False,unique=True)
    estado = db.Column(db.Enum('PENDIENTE','ACTIVA','COMPLETADA','EXPIRADA'),nullable=False,default='PENDIENTE')
    expira_en = db.Column(db.DateTime,nullable=False)
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

    # relacion operador_id
    operador = db.relationship("Usuario",backref="sesiones_kioscos")
    # relacion padron_id
    padron = db.relationship("PadronElectoral",backref="sesiones_kiosco")
    # relacion kiosco_id
    kiosco = db.relationship("Kiosco",backref="sesiones")