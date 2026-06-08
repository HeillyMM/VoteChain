"""kiosk.py (ruta nueva) — operador ingresa CI → llama a segip_service → habilita kiosco → 
genera token de sesión de un solo uso en sesiones_kiosco. """

from flask import Blueprint, request, jsonify

bp_kiosk = Blueprint("bp_kiosk", __name__)

@bp_kiosk.route("/estado")
def estado():
    return jsonify({"kiosk": "activo"})