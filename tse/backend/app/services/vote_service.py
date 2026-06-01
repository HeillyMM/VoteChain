import secrets
from datetime import datetime
from app.extensions import db
from app.models.padron import PadronElectoral
from app.models.padron import SesionKiosco
from app.blockchain.chain import Blockchain
from app.blockchain.crypto import VoteCipher
from app.services.audit_service import AuditService
from app.services.conteo_service import ConteoService

class VoteService:

    @staticmethod
    def emitir_voto(padron_id, candidato_id, eleccion_id, session_token):

        sesion = SesionKiosco.query.filter_by(token_hash=session_token).first()
        if not sesion or sesion.estado != "ACTIVA":
            raise Exception("Sesión inválida")

        padron = PadronElectoral.query.get(padron_id)
        if padron.ya_voto:
            raise Exception("Ya votó")

        cipher = VoteCipher()
        encrypted_vote = cipher.encrypt(candidato_id, eleccion_id)

        chain = Blockchain.get_instance(eleccion_id)
        block = chain.add_transaction({
            "padron_id": padron_id,
            "candidato_id": candidato_id,
            "voto": encrypted_vote
        })

        # 5. marcar votante
        padron.ya_voto = True
        padron.hora_voto = datetime.utcnow()

        # 6. cerrar sesión kiosco
        sesion.estado = "COMPLETADA"

        db.session.commit()

        # 7. OBSERVERS
        ConteoService.recalcular(eleccion_id)
        AuditService.registrar_accion(
            usuario_id=sesion.operador_id,
            eleccion_id=eleccion_id,
            accion="VOTO_EMITIDO",
            descripcion=f"Padron {padron_id}",
            ip="kiosk"
        )

        return {
            "block_hash": block["hash"],
            "recibo": secrets.token_hex(8)
        }