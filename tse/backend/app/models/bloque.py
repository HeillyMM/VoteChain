# Tabla blockchain_bloque
from app.extensions import db
from datetime import datetime

class BlockchainBloque(db.Model):
    __tablename__ = "blockchain_bloques"

    __table_args__ = (
    db.UniqueConstraint(
        'eleccion_id',
        'block_index',
        name='uq_block_index_eleccion'
    ),
    )

    id = db.Column(db.Integer,primary_key=True)
    eleccion_id = db.Column(db.Integer,db.ForeignKey('elecciones.id',ondelete='CASCADE'),nullable=False)
    block_index = db.Column(db.Integer,nullable=False)
    prev_hash = db.Column(db.String(64),nullable=False)
    block_hash = db.Column(db.String(64),nullable=False,unique=True)
    merkle_root = db.Column(db.String(64),nullable=False)
    total_tx = db.Column(db.Integer,nullable=False,default=0)
    nonce = db.Column(db.Integer,nullable=False,default=0)
    timestamp = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

    eleccion = db.relationship("Eleccion",backref="bloques")