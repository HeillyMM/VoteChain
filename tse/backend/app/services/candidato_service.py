from app.extensions import db
from app.models.candidate import Candidato

class CandidatoService:

    @staticmethod
    def listar():
        return Candidato.query.all()

    @staticmethod
    def obtener_por_id(id):
        return Candidato.query.get(id)

    @staticmethod
    def crear(
        eleccion_id,
        numero_lista,
        sigla_partido,
        nombre_partido,
        nombres,
        apellido_paterno,
        apellido_materno,
        formula_nombres,
        formula_apellido_paterno,
        logo_partido,
        foto_candidato,
        color_partido,
        propuesta_breve
    ):
        candidato = Candidato(
            eleccion_id=eleccion_id,
            numero_lista=numero_lista,
            sigla_partido=sigla_partido,
            nombre_partido=nombre_partido,
            nombres=nombres,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            formula_nombres=formula_nombres,
            formula_apellido_paterno=formula_apellido_paterno,
            logo_partido=logo_partido,
            foto_candidato=foto_candidato,
            color_partido=color_partido,
            propuesta_breve=propuesta_breve,
            activo=True
        )

        db.session.add(candidato)
        db.session.commit()
        return candidato

    @staticmethod
    def toggle_activo(id):
        candidato = Candidato.query.get(id)
        if not candidato:
            return None

        candidato.activo = not candidato.activo
        db.session.commit()
        return candidato

    @staticmethod
    def eliminar(id):
        candidato = Candidato.query.get(id)
        if not candidato:
            return None

        db.session.delete(candidato)
        db.session.commit()
        return True