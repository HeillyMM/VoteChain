from flask import session
from flask_login import login_user
from app.extensions import bcrypt, db
from app.models.usuario import Usuario

class AuthService:

# check
    @staticmethod
    def autenticar(email, password):

        usuario = Usuario.query.filter_by(email=email,activo=True).first()

        if not usuario or not bcrypt.check_password_hash(usuario.password_hash,password):
            return None

        return usuario

    @staticmethod
    def login(email: str, password: str):

        usuario = AuthService.autenticar(email,password)
        if not usuario:
            return None
        
        login_user(usuario)
        return usuario

# Check
    @staticmethod
    def crear_usuario(ci,nombres,apellidos,email,password,rol_id):

        existe = Usuario.query.filter((Usuario.email == email) | (Usuario.ci == ci)).first()
        if existe:
            raise ValueError("Ya existe un usuario con ese CI o Email")

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        usuario = Usuario(
            ci=ci,
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            password_hash=password_hash,
            rol_id=rol_id
        )

        db.session.add(usuario)
        db.session.commit()

        return usuario

    @staticmethod
    def cambiar_password(usuario_id,nueva_password):

        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")

        usuario.password_hash = bcrypt.generate_password_hash(nueva_password).decode("utf-8")
        db.session.commit()

        return True
    
    @staticmethod
    def editar_usuario(ci,nombres,apellidos,email,password,rol_id,usuario_id):
        usuario = Usuario.query.get(usuario_id)

        usuario.ci = ci
        usuario.nombres = nombres
        usuario.apellidos = apellidos
        usuario.email = email
        usuario.password = password
        usuario.rol_id = rol_id
        
        db.session.commit()

    @staticmethod
    def eliminar(id):
        usuario = Usuario.query.get(id)
        db.session.delete(usuario)
        db.session.commit()