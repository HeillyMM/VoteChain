from flask import Blueprint, request, jsonify

bp_kiosk = Blueprint("kiosk", __name__)

@bp_kiosk.route("/estado")
def estado():
    return jsonify({"kiosk": "activo"})