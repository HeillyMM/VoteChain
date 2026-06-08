"""elections.py — CRUD de elecciones (crear, activar, cerrar, suspender). 
Solo admin. Al crear genera par de claves RSA y las guarda en la tabla elecciones. """

from flask import Blueprint, render_template, request, redirect, url_for, session,flash
from app.services.election_service import EleccionService
from datetime import datetime
from app.blockchain.crypto import generar_par_claves_eleccion

bp_eleccion = Blueprint("bp_eleccion", __name__, url_prefix="/elecciones")


@bp_eleccion.route("/")
def index():
    EleccionService.actualizar_estado()
    eleccion_principal,otras_elecciones = EleccionService.listar_elecciones()
    return render_template("admin/dashboard.html", eleccion_principal=eleccion_principal,otras_elecciones=otras_elecciones)


@bp_eleccion.route("/crear", methods=["GET", "POST"])
def crear():
    if request.method == "GET":
        return render_template("admin/election_form.html")
    try:
        fecha_fin_raw = request.form.get("fecha_fin")
        EleccionService.crear(
            codigo = request.form.get("codigo"),
            titulo = request.form.get("titulo"),
            descripcion = request.form.get("descripcion"),
            tipo = request.form.get("tipo"),
            fecha_inicio = datetime.fromisoformat(request.form.get("fecha_inicio")),
            fecha_fin = datetime.fromisoformat(fecha_fin_raw) if fecha_fin_raw else None,
            created_by = session.get("user_id")
        )
        return redirect(url_for("bp_eleccion.index"))
    
    except ValueError as e:
        flash(str(e),"danger")
        return render_template("admin/election_form.html")

@bp_eleccion.route("/editar/<int:id>",methods=['GET','POST'])
def editar(id):
    if request.method == 'GET':
        eleccion = EleccionService.obtener_por_id(id)
        return render_template("/admin/election_edit_form.html",eleccion=eleccion)
    fecha_fin_raw = request.form.get("fecha_fin")
    EleccionService.editar(
        codigo = request.form.get("codigo"),
        titulo = request.form.get("titulo"),
        descripcion = request.form.get("descripcion"),
        tipo = request.form.get("tipo"),
        estado = request.form.get("estado"),
        fecha_inicio = datetime.fromisoformat(request.form.get("fecha_inicio")),
        fecha_fin = datetime.fromisoformat(fecha_fin_raw) if fecha_fin_raw else None,
        eleccion_id=id
    )
    return redirect(url_for('bp_eleccion.dashboard',eleccion_id=id))

@bp_eleccion.route("/eliminar/<int:id>")
def eliminar(id):
    EleccionService.eliminar(id)
    return redirect(url_for('bp_eleccion.index'))

@bp_eleccion.route("/dashboard/<int:eleccion_id>")
def dashboard(eleccion_id):
    eleccion = EleccionService.obtener_por_id(eleccion_id)
    return render_template("admin/dashboard_eleccion.html",eleccion=eleccion)