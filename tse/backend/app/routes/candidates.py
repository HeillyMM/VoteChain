from flask import Blueprint, render_template, request, redirect, url_for
from app.services.candidato_service import CandidatoService
from app.services.election_service import EleccionService
from werkzeug.utils import secure_filename
import os

bp_candidato = Blueprint("bp_candidato", __name__, url_prefix="/candidatos")


@bp_candidato.route("/<int:eleccion_id>")
def index(eleccion_id):
    candidatos = CandidatoService.listar(eleccion_id)
    eleccion = EleccionService.obtener_por_id(eleccion_id)

    return render_template("admin/candidates/candidates.html",candidatos=candidatos,eleccion=eleccion)


@bp_candidato.route("/nuevo/<int:eleccion_id>", methods=["GET", "POST"])
def create(eleccion_id):

    if request.method == "GET":
        return render_template("admin/candidates/candidate_form.html",eleccion_id=eleccion_id)
    
    logo = request.files.get("logo_partido")
    foto = request.files.get("foto_candidato")
    
    foto_nombre = None
    logo_nombre = None

    if foto and foto.filename:
        foto_nombre = secure_filename(foto.filename)
        foto.save(os.path.join("frontend/static/img/candidatos", foto_nombre))

    if logo and logo.filename:
        logo_nombre = secure_filename(logo.filename)
        logo.save(os.path.join("frontend/static/img/partidos", logo_nombre))

    CandidatoService.crear(
        eleccion_id=eleccion_id,
        numero_lista=CandidatoService.nro_lista(eleccion_id),
        sigla_partido=request.form.get("sigla_partido"),
        nombre_partido=request.form.get("nombre_partido"),
        nombres=request.form.get("nombres"),
        apellido_paterno=request.form.get("apellido_paterno"),
        apellido_materno=request.form.get("apellido_materno"),
        formula_nombres=request.form.get("formula_nombres"),
        formula_apellido_paterno=request.form.get("formula_apellido_paterno"),
        logo_partido=logo_nombre,
        foto_candidato=foto_nombre,
        color_partido=request.form.get("color_partido"),
        propuesta_breve=request.form.get("propuesta_breve")
    )

    return redirect(url_for("bp_candidato.index",eleccion_id=eleccion_id))


@bp_candidato.route("/toggle/<int:id>")
def toggle(id):
    candidato = CandidatoService.obtener_por_id(id)
    CandidatoService.toggle_activo(id)
    return redirect(url_for("bp_candidato.index",eleccion_id=candidato.eleccion_id))


@bp_candidato.route("/editar/<int:eleccion_id>/<int:id>",methods=['GET','POST'])
def editar(eleccion_id,id):

    candidato = CandidatoService.obtener_por_id(id)
    if request.method == "GET":
        return render_template("admin/candidates/candidate_edit_form.html",eleccion_id=eleccion_id,candidato=candidato)
    
    logo = request.files.get("logo_partido")
    foto = request.files.get("foto_candidato")
    
    foto_nombre = None
    logo_nombre = None

    if foto and foto.filename:
        foto_nombre = secure_filename(foto.filename)
        foto.save(os.path.join("frontend/static/img/candidatos", foto_nombre))
    else:
        foto_nombre = candidato.foto_candidato

    if logo and logo.filename:
        logo_nombre = secure_filename(logo.filename)
        logo.save(os.path.join("frontend/static/img/partidos", logo_nombre))
    else:
        logo_nombre = candidato.logo_partido

    CandidatoService.editar(
        eleccion_id=eleccion_id,
        sigla_partido=request.form.get("sigla_partido"),
        nombre_partido=request.form.get("nombre_partido"),
        nombres=request.form.get("nombres"),
        apellido_paterno=request.form.get("apellido_paterno"),
        apellido_materno=request.form.get("apellido_materno"),
        formula_nombres=request.form.get("formula_nombres"),
        formula_apellido_paterno=request.form.get("formula_apellido_paterno"),
        logo_partido=logo_nombre,
        foto_candidato=foto_nombre,
        color_partido=request.form.get("color_partido"),
        propuesta_breve=request.form.get("propuesta_breve"),
        activo = "activo" in request.form,
        id=id
    )

    return redirect(url_for("bp_candidato.index",eleccion_id=eleccion_id))


@bp_candidato.route("/eliminar/<int:id>")
def delete(id):
    candidato = CandidatoService.obtener_por_id(id)
    eleccion_id = candidato.eleccion_id
    CandidatoService.eliminar(id)

    return redirect(url_for("bp_candidato.index",eleccion_id=eleccion_id))