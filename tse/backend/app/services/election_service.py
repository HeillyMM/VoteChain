from app.extensions import db
from app.models.election import Eleccion
from app.models.conteo import Conteo
from app.models.candidate import Candidato
from datetime import datetime

from app.blockchain.crypto import (
    generar_par_claves_eleccion, cargar_clave_privada, VoteCipher
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
    def crear(codigo, titulo, descripcion, tipo, fecha_inicio, fecha_fin, created_by):

        #claves RSA para la eleccion
        clave_publica, clave_privada = generar_par_claves_eleccion()
        eleccion = Eleccion(
            codigo=codigo,
            titulo=titulo,
            descripcion=descripcion,
            tipo=tipo,
            estado="CONFIGURACION",
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            created_by=created_by
        )

        db.session.add(eleccion)
        db.session.commit()
        return eleccion

    @staticmethod
    def cerrar(id):
        eleccion = Eleccion.query.get(id)
        if not eleccion:
            return None

        eleccion.estado = "CERRADA"
        db.session.commit()
        return eleccion