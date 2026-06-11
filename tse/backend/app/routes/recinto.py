from flask import render_template,redirect,url_for,flash,Blueprint,request,abort
from flask_login import login_required,current_user
from app.services.recinto_service import RecintoService
from app.services.election_service import EleccionService
from app.services.padron_service import PadronService

bp_recinto = Blueprint("bp_recinto",__name__,url_prefix="/recintos")

@bp_recinto.route("/")
@login_required
def todos_recintos():
    if current_user.rol_id != 1:
        abort(403)
    recintos = RecintoService.listar_todos_recintos()
    departamentos = RecintoService.listar_departamentos()
    return render_template("admin/recintos/recintos.html",recintos=recintos,departamentos=departamentos,modo_admin=True)


@bp_recinto.route("/crear",methods=['GET','POST'])
@login_required
def crear():
    if current_user.rol_id != 1:
        abort(403)
    if request.method == 'GET':
        departamentos = RecintoService.listar_departamentos()
        return render_template("admin/recintos/recinto_form.html",departamentos=departamentos)
    
    codigo = request.form.get("codigo")
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    municipio = request.form.get("municipio")
    departamento_id = request.form.get("departamento_id")
    total_mesas = request.form.get("total_mesas")
    
    if RecintoService.existe_recinto(codigo=codigo,nombre=nombre,direccion=direccion,municipio=municipio,
                                     departamento_id=departamento_id,total_mesas=total_mesas):
        flash("El recinto ya existen en la base de datos","danger")
        return redirect(url_for('bp_recinto.crear'))

    RecintoService.crear(codigo=codigo,nombre=nombre,direccion=direccion,
                         municipio=municipio,departamento_id=departamento_id,total_mesas=total_mesas)
    
    return redirect(url_for('bp_recinto.todos_recintos'))


@bp_recinto.route("/editar/<int:recinto_id>",methods=['GET','POST'])
@login_required
def editar(recinto_id):
    if current_user.rol_id != 1:
        abort(403)
    if request.method == 'GET':
        recinto = RecintoService.obtener_por_id(recinto_id)
        departamentos = RecintoService.listar_departamentos()
        return render_template("admin/recintos/recinto_edit_form.html",recinto=recinto,departamentos=departamentos)
    elif request.method == 'POST':
        codigo = request.form.get("codigo")
        nombre = request.form.get("nombre")
        direccion = request.form.get("direccion")
        municipio = request.form.get("municipio")
        departamento_id = request.form.get("departamento_id")
        total_mesas = request.form.get("total_mesas")
        activo = bool(int(request.form.get("activo")))
        recinto = RecintoService.obtener_por_id(recinto_id)
        
        if recinto.activo and not activo:
            print("reasignando")
            PadronService.reasignar(recinto_id)
        
        RecintoService.editar(codigo=codigo,nombre=nombre,direccion=direccion,
        municipio=municipio,departamento_id=departamento_id,total_mesas=total_mesas,activo=activo,recinto_id=recinto_id)
        
        return redirect(url_for('bp_recinto.todos_recintos'))

@bp_recinto.route("/eliminar/<int:recinto_id>")
@login_required
def eliminar(recinto_id):
    if current_user.rol_id != 1:
        abort(403)
    RecintoService.eliminar(recinto_id)
    return redirect(url_for('bp_recinto.todos_recintos'))



@bp_recinto.route("/recinto_eleccion/<int:eleccion_id>")
@login_required
def recinto_eleccion(eleccion_id):
    if current_user.rol_id != 1:
        abort(403)
    recintos = RecintoService.listar_recintos_eleccion(eleccion_id=eleccion_id)
    departamentos = RecintoService.listar_departamentos()
    return render_template("admin/recintos/recintos.html",recintos=recintos,departamentos=departamentos,eleccion_id=eleccion_id,modo_admin=False)

@bp_recinto.route("/seleccion/<int:eleccion_id>",methods=['GET','POST'])
@login_required
def seleccion_recintos(eleccion_id):
    if current_user.rol_id != 1:
        abort(403)
    if request.method == 'GET':
        recintos = RecintoService.listar_todos_recintos()
        departamentos = RecintoService.listar_departamentos()
        eleccion = EleccionService.obtener_por_id(eleccion_id)
        return render_template("admin/recintos/seleccionar_recintos.html",recintos=recintos,departamentos=departamentos,eleccion=eleccion)

    recintos_ids = [ int(id) for id in request.form.getlist("recintos_ids")]
    RecintoService.recintos(eleccion_id=eleccion_id,recintos_ids=recintos_ids)
    return redirect(url_for('bp_recinto.recinto_eleccion',eleccion_id=eleccion_id))
