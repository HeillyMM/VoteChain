from flask import session
from app.extensions import bcrypt, db
from app.models.usuario import Usuario

class AuthService:

    @staticmethod
    def autenticar(email, password):

        usuario = Usuario.query.filter_by(
            email=email,
            activo=True
        ).first()

        if not usuario:
            return None

        if not bcrypt.check_password_hash(
            usuario.password_hash,
            password
        ):
            return None

        return usuario

    @staticmethod
    def login(email: str, password: str):

        usuario = AuthService.autenticar(
            email,
            password
        )

        if not usuario:
            return False, "Credenciales incorrectas"

        session["user_id"] = usuario.id
        session["rol_id"] = usuario.rol_id
        session["nombre"] = usuario.nombres

        return True, "Login exitoso"

    @staticmethod
    def usuario_actual():

        user_id = session.get("user_id")

        if not user_id:
            return None

        return Usuario.query.get(user_id)

    @staticmethod
    def autenticado():
        return "user_id" in session

    @staticmethod
    def tiene_rol(*roles):

        usuario = AuthService.usuario_actual()

        if not usuario:
            return False

        return usuario.rol.nombre in roles

    @staticmethod
    def crear_usuario(
        ci,
        nombres,
        apellidos,
        email,
        password,
        rol_id
    ):

        existe = Usuario.query.filter(
            (Usuario.email == email) |
            (Usuario.ci == ci)
        ).first()

        if existe:
            raise ValueError(
                "Ya existe un usuario con ese CI o Email"
            )

        password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

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
    def cambiar_password(
        usuario_id,
        nueva_password
    ):

        usuario = Usuario.query.get(usuario_id)

        if not usuario:
            raise ValueError(
                "Usuario no encontrado"
            )

        usuario.password_hash = bcrypt.generate_password_hash(
            nueva_password
        ).decode("utf-8")

        db.session.commit()

        return True