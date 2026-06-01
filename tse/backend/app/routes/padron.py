from flask import Blueprint, jsonify,render_template,redirect,url_for
from app.services.padron_service import PadronService

bp_padron = Blueprint("bp_padron", __name__)

@bp_padron.route("/importar")
def importar_padron():

    cantidad = PadronService.construir_padron()

    return redirect(url_for('bp_padron.index'))

@bp_padron.route("/")
def index():
    padron = PadronService.listar()
    return render_template("admin/padron.html", padron=padron)

