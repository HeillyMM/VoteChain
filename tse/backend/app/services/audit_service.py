import hashlib
from datetime import datetime
from app.extensions import db
from app.models.audit_log import AuditLog

class AuditService:

    @staticmethod
    def registrar_accion(usuario_id, eleccion_id, accion, descripcion=None, ip=None):
        ultimo = AuditLog.query.order_by(AuditLog.id.desc()).first()
        prev_hash = ultimo.hash_integridad if ultimo else "0"

        payload = f"{usuario_id}{eleccion_id}{accion}{descripcion}{ip}{datetime.utcnow()}{prev_hash}"
        hash_integridad = hashlib.sha256(payload.encode()).hexdigest()

        log = AuditLog(
            usuario_id=usuario_id,
            eleccion_id=eleccion_id,
            accion=accion,
            descripcion=descripcion,
            ip_hash=ip,
            hash_integridad=hash_integridad
        )

        db.session.add(log)
        db.session.commit()

        return hash_integridad