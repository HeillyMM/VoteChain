from flask import Blueprint, jsonify
from app.services.padron_service import PadronService

bp_padron = Blueprint("bp_padron", __name__)

@bp_padron.route("/importar")
def importar_padron():

    cantidad = PadronService.construir_padron()

    return jsonify({
        "mensaje": "Padrón actualizado",
        "nuevos": cantidad
    })