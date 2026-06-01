from app import create_app
from app.models.usuario import Usuario
from app.extensions import bcrypt, db

app = create_app()

with app.app_context():

    hashed = bcrypt.generate_password_hash("123").decode("utf-8")

    usuario = Usuario(
        ci="16564359",
        nombres="Helen Keilly",
        apellidos="Mamani Mollinedo",
        email="heilly.other@gmail.com",
        password_hash=hashed,
        rol_id=1
    )

    db.session.add(usuario)
    db.session.commit()

    print("Usuario creado correctamente")