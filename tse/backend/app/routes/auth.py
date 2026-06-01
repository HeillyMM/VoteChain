from flask import Blueprint, render_template, request, redirect, session, flash
from app.services.auth_service import AuthService

bp_auth = Blueprint("bp_auth", __name__)

@bp_auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("auth/login.html")

    email = request.form.get("usuario")
    password = request.form.get("password")

    user = AuthService.autenticar(email, password)

    if not user:
        flash("Credenciales incorrectas", "danger")
        return render_template("auth/login.html")

    session["user_id"] = user.id
    session["rol"] = user.rol_id
    session["email"] = user.email

    if user.rol_id == 1:
        return render_template("admin/dashboard.html")
    elif user.rol_id == 2:
        return redirect("/operador")
    else:
        return redirect("/auditor")