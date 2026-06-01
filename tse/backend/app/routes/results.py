from flask import Blueprint, jsonify
from app.services.conteo_service import ConteoService

bp_results = Blueprint("results", __name__)

@bp_results.route("/<int:eleccion_id>")
def resultados(eleccion_id):
    data = ConteoService.resultados(eleccion_id)
    return jsonify([
        {
            "candidato_id": c.candidato_id,
            "tipo": c.tipo,
            "total": c.total_votos
        } for c in data
    ])