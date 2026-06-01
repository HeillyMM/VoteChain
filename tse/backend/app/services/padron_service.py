from .segip_service import SegipService
from app.models.padron import PadronElectoral
from app.extensions import db
from email.utils import parsedate_to_datetime

class PadronService:

    @staticmethod
    def listar():
        return PadronElectoral.query.all()

    @staticmethod
    def construir_padron():

        ciudadanos = SegipService.obtener_ciudadanos()
        nuevos = 0

        for ciudadano in ciudadanos:
            existe = PadronElectoral.query.filter_by(ci=ciudadano["ci"]).first()

            if existe:
                continue
            fecha_nacimiento = parsedate_to_datetime(
                ciudadano["fecha_nacimiento"]
            ).date()
            nuevo = PadronElectoral(
                ci=ciudadano["ci"],
                nombres=ciudadano["nombres"],
                apellido_paterno=ciudadano["apellido_paterno"],
                apellido_materno=ciudadano["apellido_materno"],
                fecha_nacimiento=fecha_nacimiento,
                sexo=ciudadano["sexo"]
            )

            db.session.add(nuevo)
            nuevos +=1
        db.session.commit()
        return nuevos