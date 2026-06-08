from app.extensions import db
from app.models.election import Eleccion
from app.models.conteo import Conteo

from app.blockchain.crypto import (
    generar_par_claves_eleccion,
    cargar_clave_privada,
    VoteCipher
)

from app.blockchain.chain import Blockchain
from datetime import datetime

class EleccionService:

    @staticmethod
    def listar():
        return Eleccion.query.all()

    @staticmethod
    def obtener_por_id(id):
        return Eleccion.query.get(id)
    
    
    @staticmethod
    def actualizar_estado():
        elecciones = Eleccion.query.all()
        if not elecciones:
            return

        hoy = datetime.utcnow()

        for eleccion in elecciones:
            if eleccion.estado == "SUSPENDIDA":
                continue
            if hoy < eleccion.fecha_inicio:
                eleccion.estado = "CONFIGURACIÓN"
            elif eleccion.fecha_inicio <= hoy <= eleccion.fecha_fin:
                eleccion.estado = "ACTIVA"
            else:
                eleccion.estado = "CERRADA"
        db.session.commit()

    @staticmethod
    def listar_elecciones():
        elecciones = Eleccion.query.order_by(Eleccion.fecha_inicio.asc()).all()
        elecciones = sorted(elecciones,key=lambda e: e.estado in ["SUSPENDIDA", "CERRADA"])
        if not elecciones:
            return None, []
        if elecciones[0].estado in ["SUSPENDIDA", "CERRADA"]:
            return None, elecciones

        return elecciones[0], elecciones[1:]

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
        hoy = datetime.utcnow()

        if fecha_inicio < hoy:
            raise ValueError("No se puede crear una elección con fecha de inicio pasada.")

        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha de finalización debe ser posterior a la fecha de inicio.")

        conflicto = Eleccion.query.filter(Eleccion.fecha_inicio <= fecha_fin,Eleccion.fecha_fin >= fecha_inicio).first()

        if conflicto:
            raise ValueError(f"Las fechas se cruzan con la elección '{conflicto.titulo}'.")

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
        Blockchain.get_instance(eleccion.id)
        

    @staticmethod
    def editar(
        codigo,
        titulo,
        descripcion,
        tipo,
        fecha_inicio,
        fecha_fin,
        eleccion_id,
        estado
    ):

        eleccion = Eleccion.query.get(eleccion_id)
        eleccion.codigo=codigo
        eleccion.titulo=titulo
        eleccion.descripcion=descripcion
        eleccion.tipo=tipo
        eleccion.estado=estado
        eleccion.fecha_inicio=fecha_inicio
        eleccion.fecha_fin=fecha_fin

        db.session.commit()

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
    
    @staticmethod
    def eliminar(id):
        eleccion = Eleccion.query.get(id)
        db.session.delete(eleccion)
        db.session.commit()