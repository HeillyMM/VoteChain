from app.extensions import db
from app.models.election import Eleccion
from datetime import datetime

class EleccionService:

    @staticmethod
    def listar():
        return Eleccion.query.all()

    @staticmethod
    def obtener_por_id(id):
        return Eleccion.query.get(id)

    @staticmethod
    def crear(codigo, titulo, descripcion, tipo, fecha_inicio, fecha_fin, created_by):

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