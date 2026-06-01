from flask import Blueprint, render_template, request, redirect, url_for
from app.services.candidato_service import CandidatoService

bp_candidato = Blueprint("bp_candidato", __name__, url_prefix="/candidatos")


@bp_candidato.route("/")
def index():
    candidatos = CandidatoService.listar()
    return render_template("admin/candidates.html", candidatos=candidatos)


@bp_candidato.route("/nuevo", methods=["GET", "POST"])
def create():

    if request.method == "GET":
        from app.services.election_service import EleccionService
        elecciones = EleccionService.listar()

        return render_template(
            "admin/candidate_form.html",
            elecciones=elecciones
        )

    CandidatoService.crear(
        eleccion_id=request.form.get("eleccion_id"),
        numero_lista=request.form.get("numero_lista"),
        sigla_partido=request.form.get("sigla_partido"),
        nombre_partido=request.form.get("nombre_partido"),
        nombres=request.form.get("nombres"),
        apellido_paterno=request.form.get("apellido_paterno"),
        apellido_materno=request.form.get("apellido_materno"),
        formula_nombres=request.form.get("formula_nombres"),
        formula_apellido_paterno=request.form.get("formula_apellido_paterno"),
        logo_partido=request.form.get("logo_partido"),
        foto_candidato=request.form.get("foto_candidato"),
        color_partido=request.form.get("color_partido"),
        propuesta_breve=request.form.get("propuesta_breve")
    )

    return redirect(url_for("bp_candidato.index"))


@bp_candidato.route("/toggle/<int:id>")
def toggle(id):
    CandidatoService.toggle_activo(id)
    return redirect(url_for("bp_candidato.index"))


@bp_candidato.route("/eliminar/<int:id>")
def delete(id):
    CandidatoService.eliminar(id)
    return redirect(url_for("bp_candidato.index"))