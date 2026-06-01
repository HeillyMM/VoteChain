from flask import Blueprint, render_template, request, redirect, url_for, session
from app.services.election_service import EleccionService
from datetime import datetime

bp_eleccion = Blueprint("bp_eleccion", __name__, url_prefix="/elecciones")


@bp_eleccion.route("/")
def index():
    eleccions = EleccionService.listar()
    return render_template("admin/elections.html", eleccions=eleccions)


@bp_eleccion.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("admin/election_form.html")

    codigo = request.form.get("codigo")
    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    tipo = request.form.get("tipo")

    fecha_inicio = datetime.fromisoformat(request.form.get("fecha_inicio"))
    fecha_fin_raw = request.form.get("fecha_fin")
    fecha_fin = datetime.fromisoformat(fecha_fin_raw) if fecha_fin_raw else None

    created_by = session.get("user_id")

    EleccionService.crear(
        codigo,
        titulo,
        descripcion,
        tipo,
        fecha_inicio,
        fecha_fin,
        created_by
    )

    return redirect(url_for("bp_eleccion.index"))


@bp_eleccion.route("/close/<int:id>")
def close(id):
    EleccionService.cerrar(id)
    return redirect(url_for("bp_eleccion.index"))