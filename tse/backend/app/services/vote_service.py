# tse/backend/app/services/vote_service.py
import hashlib
import secrets
from datetime import datetime, timedelta

from app.extensions import db
from app.models.padron import PadronElectoral, SesionKiosco
from app.models.election import Eleccion
from app.models.candidate import Candidato
from app.models.bloque import BlockchainBloque
from app.models.recibo import Recibo
from app.blockchain.chain import Blockchain
from app.blockchain.crypto import (
VoteCipher, generar_voter_token, generar_codigo_recibo, cargar_clave_publica)
from app.services.audit_service import AuditService


class VoteService:

    # Crear una sesión temporal para que el ciudadano pueda votar
    @staticmethod
    def crear_sesion_kiosco(padron_id: int, kiosco_id: int, operador_id: int) -> str:

        # Cerrar sesiones activas anteriores
        SesionKiosco.query.filter_by(
            padron_id=padron_id,
            estado='ACTIVA'
        ).update({'estado': 'EXPIRADA'})

        token      = secrets.token_hex(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        sesion = SesionKiosco(
            operador_id=operador_id,
            padron_id=padron_id,
            kiosco_id=kiosco_id,
            token_hash=token_hash,
            estado='ACTIVA',
            expira_en=datetime.utcnow() + timedelta(minutes=5)
        )

        db.session.add(sesion)
        db.session.commit()

        AuditService.registrar_accion(
            usuario_id=operador_id,
            eleccion_id=None,
            accion='KIOSCO_HABILITADO',
            descripcion=f'Padrón {padron_id} habilitado en kiosco {kiosco_id}'
        )

        return token

    # Verifica que el token siga siendo válido
    @staticmethod
    def validar_token(token: str) -> dict:

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        sesion = SesionKiosco.query.filter_by(
            token_hash=token_hash,
            estado='ACTIVA'
        ).first()

        if not sesion:
            return {'ok': False, 'error': 'Sesión inválida o ya utilizada'}

        if datetime.utcnow() > sesion.expira_en:
            sesion.estado = 'EXPIRADA'
            db.session.commit()
            return {'ok': False, 'error': 'La sesión expiró. El operador debe volver a habilitar'}

        return {'ok': True, 'sesion': sesion}

    # Registra el voto en la blockchain
    @staticmethod
    def emitir_voto(token: str, candidato_id: int, eleccion_id: int) -> dict:

        # Validar sesión
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        sesion = SesionKiosco.query.filter_by(
            token_hash=token_hash,
            estado='ACTIVA'
        ).first()

        if not sesion:
            return {'ok': False, 'error': 'Sesión inválida o ya utilizada'}

        if datetime.utcnow() > sesion.expira_en:
            sesion.estado = 'EXPIRADA'
            db.session.commit()
            return {'ok': False, 'error': 'Sesión expirada'}

        # Verificar que el ciudadano no haya votado
        padron = PadronElectoral.query.get(sesion.padron_id)

        if not padron:
            return {'ok': False, 'error': 'Votante no encontrado en el padrón'}

        if padron.ya_voto:
            return {'ok': False, 'error': 'El ciudadano ya emitió su voto'}

        # Verificar candidato
        candidato = Candidato.query.filter_by(
            id=candidato_id,
            eleccion_id=eleccion_id,
            activo=True
        ).first()

        if not candidato:
            AuditService.registrar_accion(
                usuario_id=sesion.operador_id,
                eleccion_id=eleccion_id,
                accion='VOTO_RECHAZADO',
                descripcion=f'Candidato {candidato_id} inválido para elección {eleccion_id}'
            )

            return {'ok': False, 'error': 'Candidato no válido para esta elección'}

        # Verificar elección
        eleccion = Eleccion.query.get(eleccion_id)

        if not eleccion or eleccion.estado != 'ACTIVA':
            return {'ok': False, 'error': 'La elección no está activa'}

        # Cifrar el voto
        clave_publica = cargar_clave_publica(eleccion.clave_publica_pem)

        cipher = VoteCipher()
        encrypted_vote = cipher.encrypt(candidato_id, clave_publica)

        # Generar identificadores anónimos
        voter_token = generar_voter_token(padron.id)
        codigo_recibo = generar_codigo_recibo()

        # Crear transacción
        transaction = {
            'voter_token': voter_token,
            'encrypted_vote': encrypted_vote,
            'election_id': eleccion_id,
            'receipt': codigo_recibo
        }

        # Registrar en blockchain
        blockchain = Blockchain.get_instance(eleccion_id)
        nuevo_bloque = blockchain.add_votes(transaction)

        # Guardar información del bloque
        bloque_idx = BlockchainBloque(
            eleccion_id=eleccion_id,
            block_index=nuevo_bloque.index,
            prev_hash=nuevo_bloque.previous_hash,
            block_hash=nuevo_bloque.hash,
            merkle_root=nuevo_bloque.merkle_root,
            total_tx=len(nuevo_bloque.transactions),
            nonce=nuevo_bloque.nonce
        )

        db.session.add(bloque_idx)

        # Marcar al ciudadano como votante
        padron.ya_voto = True
        padron.hora_voto = datetime.utcnow()
        padron.habilitado_por = sesion.operador_id

        # Guardar recibo
        recibo = Recibo(
            padron_id=padron.id,
            eleccion_id=eleccion_id,
            codigo_recibo=codigo_recibo,
            block_hash=nuevo_bloque.hash,
            impreso=False
        )

        db.session.add(recibo)

        # Cerrar la sesión utilizada
        sesion.estado = 'COMPLETADA'

        # Guardar cambios
        db.session.commit()

        # Actualizar conteo de votos
        try:
            from app.services.conteo_service import ConteoService

            ConteoService.actualizar_con_bloque(
                eleccion_id=eleccion_id,
                bloque=nuevo_bloque,
                clave_privada_pem=eleccion.clave_privada_pem
            )

        except Exception as e:
            print(f'[VoteService] Advertencia en conteo: {e}')

        # Registrar auditoría
        AuditService.registrar_accion(
            usuario_id=sesion.operador_id,
            eleccion_id=eleccion_id,
            accion='VOTO_EMITIDO',
            descripcion=f'Bloque {nuevo_bloque.index} · Hash {nuevo_bloque.hash[:16]}...'
        )

        return {
            'ok': True,
            'block_hash': nuevo_bloque.hash,
            'block_index': nuevo_bloque.index,
            'codigo_recibo': codigo_recibo
        }