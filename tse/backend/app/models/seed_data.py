from app import create_app
from app.extensions import db, bcrypt
from app.models.usuario import Usuario

app = create_app()

with app.app_context():
    contrasena = bcrypt.generate_password_hash("123").decode("utf-8")

    usuario1 = Usuario(
        ci="16564359",
        nombres="Helen Keilly",
        apellidos="Mamani Mollinedo",
        email="helenkeylli@gmail.com",
        password_hash=contrasena,
        rol_id=1
    )

    usuario2 = Usuario(
        ci="64155610",
        nombres="Limber Limachi",
        apellidos="Perez",
        email="limberlimachi@gmail.com",
        password_hash=contrasena,
        rol_id=2
    )

    usuario3 = Usuario(
        ci="79124712",
        nombres="Melany Aidee",
        apellidos="Gonzales",
        email="melanyaidee@gmail.com",
        password_hash=contrasena,
        rol_id=3
    )

    db.session.add_all([usuario1, usuario2, usuario3])
    db.session.commit()

    print("Usuarios agregados correctamente")