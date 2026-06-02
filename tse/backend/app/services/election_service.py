from app.extensions import db
from app.models.election import Eleccion
from app.models.conteo import Conteo

from app.blockchain.crypto import (
    generar_par_claves_eleccion,
    cargar_clave_privada,
    VoteCipher
)

from app.blockchain.chain import Blockchain


class EleccionService:

    @staticmethod
    def listar():
        return Eleccion.query.all()

    @staticmethod
    def obtener_por_id(id):
        return Eleccion.query.get(id)

    @staticmethod
    def crear(
        codigo,
        titulo,
        descripcion,
        tipo,
        fecha_inicio,
        fecha_fin,
        created_by
    ):

        # Generar claves RSA para la elección
        clave_publica, clave_privada = generar_par_claves_eleccion()

        eleccion = Eleccion(
            codigo=codigo,
            titulo=titulo,
            descripcion=descripcion,
            tipo=tipo,
            estado="CONFIGURACION",
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            clave_publica_pem=clave_publica,
            clave_privada_pem=clave_privada,
            created_by=created_by
        )

        db.session.add(eleccion)
        db.session.commit()

        # Crear blockchain y bloque génesis
        Blockchain.get_instance(eleccion.id)

        return eleccion

    @staticmethod
    def cerrar(id):

        eleccion = Eleccion.query.get(id)

        if not eleccion:
            return None

        blockchain = Blockchain.get_instance(id)

        private_key = cargar_clave_privada(
            eleccion.clave_privada_pem
        )

        cipher = VoteCipher()

        votos = {}

        for tx in blockchain.get_transactions():

            candidato_id = cipher.decrypt(
                tx["encrypted_vote"],
                private_key
            )

            votos[candidato_id] = (
                votos.get(candidato_id, 0) + 1
            )

        # Limpiar conteos anteriores
        Conteo.query.filter_by(
            eleccion_id=id
        ).delete()

        # Crear nuevos conteos
        for candidato_id, total in votos.items():

            conteo = Conteo(
                eleccion_id=id,
                candidato_id=candidato_id,
                tipo="VALIDO",
                total_votos=total
            )

            db.session.add(conteo)

        eleccion.estado = "CERRADA"

        db.session.commit()

        return eleccion