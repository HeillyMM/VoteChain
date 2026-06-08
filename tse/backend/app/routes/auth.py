from flask import Blueprint, render_template, request, flash,abort,redirect,url_for
from flask_login import logout_user,login_required,current_user
from app.services.auth_service import AuthService
from app.models.usuario import Usuario
from app.models.recinto import Recinto
from app.routes.elections import bp_eleccion

bp_auth = Blueprint("bp_auth", __name__)

@bp_auth.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    user = AuthService.login(email, password)
    if not user:
        flash("Credenciales incorrectas", "danger")
        return render_template("auth/login.html")

    if current_user.rol_id == 1:
        return redirect(url_for('bp_eleccion.index'))
    elif current_user.rol_id == 2:
        return render_template("operator/dashboard.html")
    else:
        return render_template("audit/dashboard.html")
    
@bp_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("auth/login.html")
    
@bp_auth.route("/register",methods=['GET','POST'])
@login_required
def register():
    if current_user.rol_id != 1:
        abort(403)
    if request.method == 'POST':
            try:
                ci = request.form.get('ci')
                nombres = request.form.get('nombres')
                apellidos = request.form.get('apellidos')
                email = request.form.get('email')
                password = request.form.get('password')
                rol_id = request.form.get('rol_id')

                AuthService.crear_usuario(ci,nombres,apellidos,email,password,rol_id)
                flash("Usuario registrado exitosamente","success")

            except ValueError as e:
                flash(str(e),"error")

            return redirect(url_for('bp_auth.usuarios'))
    recintos = Recinto.query.all()
    return render_template("admin/users/create_user.html",recintos=recintos)

@bp_auth.route("/change_password/<int:id>",methods=['GET','POST'])
@login_required
def change_password(id):
    if current_user.rol_id != 1:
        abort(403)
    if request.method == 'POST':
        try:
            password = request.form.get('password')
            AuthService.cambiar_password(id,password)

            flash("Contraseña cambiada exitosamente","success")

        except ValueError as e:
            flash(str(e),"error")
            
            return redirect(url_for('bp_auth.usuarios'))
    return render_template("admin/users/change_password.html")

@bp_auth.route("/usuarios")
def usuarios():
    usuarios = Usuario.query.all()
    return render_template("admin/users/users.html",usuarios=usuarios)

@bp_auth.route("/editar/<int:usuario_id>",methods=['GET','POST'])
def editar(usuario_id):
    if request.method == 'POST':
        ci = request.form.get('ci')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        email = request.form.get('email')
        password = request.form.get('password')
        rol_id = request.form.get('rol_id')

        AuthService.editar_usuario(ci=ci,nombres=nombres,apellidos=apellidos,email=email,password=password,rol_id=rol_id,usuario_id=usuario_id)
        return redirect(url_for('bp_auth.usuarios'))

    usuario = Usuario.query.get(usuario_id)
    recintos = Recinto.query.all()
    return render_template("admin/users/edit_user.html",usuario=usuario,recintos=recintos)

@bp_auth.route("/eliminar/<int:usuario_id>")
def eliminar(usuario_id):
    AuthService.eliminar(usuario_id)
    return redirect(url_for('bp_auth.usuarios'))