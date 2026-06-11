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
    def reasignar(recinto_id):
        recinto_inactivo = Recinto.query.get(recinto_id)
        elecciones = Eleccion.query.filter_by(estado="CONFIGURACION").all()
        for eleccion in elecciones:
            if recinto_inactivo not in eleccion.recintos:
                continue
            eleccion.recintos.remove(recinto_inactivo)
            votantes = PadronElectoral.query.filter_by(recinto_id=recinto_id,eleccion_id=eleccion.id).all()
            for votante in votantes:
                nuevo_recinto_id, nueva_mesa = PadronService.asignar_recinto(recinto_inactivo.departamento_id,eleccion.id)
                votante.recinto_id = nuevo_recinto_id
                votante.mesa_numero = nueva_mesa
        db.session.commit()

    @staticmethod
    def asignar_recinto(departamento_id, eleccion_id, capacidad_por_mesa=5):
        print(departamento_id,eleccion_id)
        eleccion = Eleccion.query.get(eleccion_id)
        print([recinto.nombre for recinto in eleccion.recintos])
        recintos_departamento = [recinto for recinto in eleccion.recintos if str(recinto.departamento_id) == str(departamento_id)]
        print(recintos_departamento)
        if not recintos_departamento:
            return None, None
        for recinto in recintos_departamento:
            asignados = PadronElectoral.query.filter_by(recinto_id=recinto.id,eleccion_id=eleccion_id).count()
            print(f"total asignados: {asignados}")
            capacidad_total = recinto.total_mesas * capacidad_por_mesa
            print(f"capacidad total: {capacidad_total}")
            if asignados < capacidad_total:
                print("aún se puede asignar")
                mesa = (asignados // capacidad_por_mesa) + 1
                return recinto.id, mesa
        return None, None
    
    @staticmethod
    def reasignar_recinto(eleccion_id):
        padrones_sin_recinto = PadronElectoral.query.filter_by(eleccion_id=eleccion_id,recinto_id=None).all()
        sin_recintos = 0
        for padron in padrones_sin_recinto:
            recinto_id,mesa = PadronService.asignar_recinto(departamento_id=padron.departamento_id,eleccion_id=eleccion_id)
            if recinto_id is None:
                sin_recintos+=1
            padron.recinto_id = recinto_id
            padron.mesa_numero = mesa
            db.session.commit()
        if sin_recintos !=0:
            raise ValueError(f"No hay existen recintos o todos están llenos para {sin_recintos} personas")
    
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