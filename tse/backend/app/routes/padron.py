from flask import Blueprint, jsonify,render_template,redirect,url_for,request
from app.services.padron_service import PadronService
from app.services.segip_service import SegipService

bp_padron = Blueprint("bp_padron", __name__)

@bp_padron.route("/importar")
def importar_padron():
    return redirect(url_for('bp_padron.index'))

@bp_padron.route("/")
def index():
    padron = PadronService.listar()
    return render_template("admin/padron.html", padron=padron)

@bp_padron.route("/verificar", methods=["POST","GET"])
def verificar():
    if request.method == 'GET':
        return render_template("operator/verificar.html",ciudadano="",buscado="")
    ci = request.form.get("ci", "").strip()
    ciudadano = SegipService.verificar_ci(ci)
    return render_template(
        "operator/verificar.html",
        ciudadano=ciudadano,
        buscado=ci
    )