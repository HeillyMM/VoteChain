from flask import Blueprint, request, jsonify
from app.services.vote_service import VoteService

bp_votes = Blueprint("votes", __name__)

@bp_votes.route("/emitir", methods=["POST"])
def emitir():
    data = request.json

    result = VoteService.emitir_voto(
        data["padron_id"],
        data["candidato_id"],
        data["eleccion_id"],
        data["token"]
    )

    return jsonify(result)