# Check
from flask import Blueprint, render_template, redirect, url_for, request, flash,abort
from flask_login import login_required,current_user
from app.services.padron_service import PadronService
from app.services.segip_service import SegipService
from app.models.election import Eleccion
from app.models.usuario import Usuario

bp_padron = Blueprint("bp_padron", __name__)

@bp_padron.route("/<int:id_eleccion>")
@login_required
def index(id_eleccion):
    if current_user.rol_id != 1 and current_user.rol_id !=2:
        abort(403)
    if current_user.rol_id == 2:
        recinto_id = Usuario.query.get(current_user.id).recinto.id
        padron = PadronService.listar_operador(id_eleccion,recinto_id) 
    else:
        padron = PadronService.listar(id_eleccion)
    return render_template("admin/padron.html", padron=padron, id_eleccion=id_eleccion)

@bp_padron.route("/importar/<int:id_eleccion>")
@login_required
def importar_padron(id_eleccion):
    if current_user.rol_id !=1:
        abort(403)
    recintos = Eleccion.query.get(id_eleccion).recintos
    if not recintos:
        flash("No hay recintos registrados. Crea recintos antes de construir el padrón.", "danger")
        return redirect(url_for("bp_padron.index", id_eleccion=id_eleccion))
    
    try:
        resultado = PadronService.construir_padron(id_eleccion)
        flash(f"Padrón construido. Agregados: {resultado['agregados']}. "f"Sin recinto disponible: {resultado['sin_recinto']}.","success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("bp_padron.index", id_eleccion=id_eleccion))


@bp_padron.route("/verificar/<int:eleccion_id>", methods=["GET", "POST"])
@login_required
def verificar(eleccion_id):
    if current_user.rol_id != 1 and current_user.rol_id !=2:
        abort(403)
    if request.method == "GET":
        return render_template("operator/verificar.html",ciudadano=None,padron=None,buscado="",eleccion_id=eleccion_id)

    ci = request.form.get("ci")
    if not ci:
        flash("Ingresa una cédula de identidad.", "warning")
        return redirect(url_for("bp_padron.verificar", eleccion_id=eleccion_id))

    ciudadano_segip = SegipService().obtener_ciudano(ci=ci)
    padron = PadronService.buscar_por_ci(ci, eleccion_id)

    return render_template("operator/verificar.html",ciudadano=ciudadano_segip,padron=padron,buscado=ci,eleccion_id=eleccion_id)
