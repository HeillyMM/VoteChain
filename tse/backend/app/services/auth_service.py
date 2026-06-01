from app.models.usuario import Usuario
from flask_bcrypt import check_password_hash

class AuthService:

    @staticmethod
    def autenticar(email, password):
        user = Usuario.query.filter_by(email=email).first()

        if not user:
            return None

        if not check_password_hash(user.password_hash, password):
            return None

        return user