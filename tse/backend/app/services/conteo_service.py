from app.extensions import db
from app.models.conteo import Conteo
from app.models.candidate import Candidato
from app.blockchain.chain import Blockchain

class ConteoService:

    @staticmethod
    def recalcular(eleccion_id):
        chain = Blockchain.get_instance(eleccion_id)

        Conteo.query.filter_by(eleccion_id=eleccion_id).delete()

        for block in chain.chain:
            for tx in block["transactions"]:
                candidato_id = tx.get("candidato_id")

                if candidato_id is None:
                    tipo = "BLANCO"
                else:
                    tipo = "VALIDO"

                conteo = Conteo.query.filter_by(
                    eleccion_id=eleccion_id,
                    candidato_id=candidato_id,
                    tipo=tipo
                ).first()

                if not conteo:
                    conteo = Conteo(
                        eleccion_id=eleccion_id,
                        candidato_id=candidato_id,
                        tipo=tipo,
                        total_votos=0
                    )
                    db.session.add(conteo)

                conteo.total_votos += 1

        db.session.commit()

    @staticmethod
    def resultados(eleccion_id):
        return Conteo.query.filter_by(eleccion_id=eleccion_id).all()