from datetime import datetime, date
from .segip_service import SegipService
from app.models.padron import PadronElectoral
from app.models.recinto import Recinto
from app.models.election import Eleccion
from app.extensions import db
from email.utils import parsedate_to_datetime

class PadronService:

    @staticmethod
    def listar(eleccion_id):
        return PadronElectoral.query.filter_by(eleccion_id=eleccion_id).all()

    @staticmethod
    def listar_operador(eleccion_id,recinto_id):
        return PadronElectoral.query.filter_by(eleccion_id=eleccion_id,recinto_id=recinto_id)

    @staticmethod
    def construir_padron(eleccion_id):
        ciudadanos = SegipService().obtener_ciudadanos()
        nuevos = 0
        sin_recinto = 0

        for ciudadano in ciudadanos:

            try:
                fecha_nacimiento = parsedate_to_datetime(ciudadano["fecha_nacimiento"]).date()
            except (ValueError, KeyError):
                print("Fecha inválida", flush=True)
                continue

            edad = (date.today() - fecha_nacimiento).days // 365
            if edad < 18 or not ciudadano.get("vivo") or not ciudadano.get("valido"):
                continue

            existe = PadronElectoral.query.filter_by(ci=ciudadano["ci"],eleccion_id=eleccion_id).first()
            if existe:
                continue

            recinto_id, mesa = PadronService.asignar_recinto(departamento_id=ciudadano["departamento_id"],eleccion_id=eleccion_id)
            if recinto_id is None:
                sin_recinto += 1
                continue

            nuevo = PadronElectoral(
                eleccion_id=eleccion_id,
                ci=ciudadano["ci"],
                complemento=ciudadano.get("complemento"),
                nombres=ciudadano["nombres"],
                apellido_paterno=ciudadano["apellido_paterno"],
                apellido_materno=ciudadano.get("apellido_materno"),
                fecha_nacimiento=fecha_nacimiento,
                sexo=ciudadano["sexo"],
                departamento_id=ciudadano["departamento_id"],
                recinto_id=recinto_id,
                mesa_numero=mesa,
            )
            db.session.add(nuevo)
            nuevos += 1

        db.session.commit()
        return {"agregados": nuevos,"sin_recinto": sin_recinto}

    @staticmethod
    def asignar_recinto(departamento_id, eleccion_id, capacidad_por_mesa=5):

        eleccion = Eleccion.query.get(eleccion_id)
        recintos_departamento = []

        for recinto in eleccion.recintos:
            print (recinto.departamento_id)
            if str(recinto.departamento_id) == str(departamento_id):
                recintos_departamento.append(recinto)

        if not recintos_departamento:
            return None, None

        for recinto in recintos_departamento:
            asignados = PadronElectoral.query.filter_by(recinto_id=recinto.id,eleccion_id=eleccion_id).count()
            capacidad_total = recinto.total_mesas * capacidad_por_mesa
            if asignados < capacidad_total:
                mesa = (asignados // capacidad_por_mesa) + 1
                return recinto.id, mesa

        recinto = recintos_departamento[-1]
        return recinto.id, recinto.total_mesas

    # ── Buscar una persona en el padrón ───────────────────────
    @staticmethod
    def buscar_por_ci(ci, eleccion_id):
        return PadronElectoral.query.filter_by(
            ci=ci,
            eleccion_id=eleccion_id,
            habilitado=True
        ).first()

    # ── Marcar como votó ──────────────────────────────────────
    @staticmethod
    def marcar_voto(padron_id, operador_id):
        padron = PadronElectoral.query.get(padron_id)
        if not padron:
            raise Exception("Persona no encontrada en el padrón.")
        if padron.ya_voto:
            raise Exception("Esta persona ya emitió su voto.")

        padron.ya_voto = True
        padron.hora_voto = datetime.utcnow()
        padron.habilitado_por = operador_id
        db.session.commit()