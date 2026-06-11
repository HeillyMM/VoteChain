from flask import Flask
from app.extensions import db,bcrypt,login_manager,migrate
from app.models import * 
import os

def create_app():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
        static_folder=os.path.join(BASE_DIR, "frontend", "static")
    )

    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from app.routes.padron import bp_padron
    from app.routes.auth import bp_auth
    from app.routes.elections import bp_eleccion
    from app.routes.candidates import bp_candidato
    from app.routes.recinto import bp_recinto

    app.register_blueprint(bp_padron, url_prefix="/padron")
    app.register_blueprint(bp_auth, url_prefix="/")
    app.register_blueprint(bp_eleccion)
    app.register_blueprint(bp_candidato)
    app.register_blueprint(bp_recinto)

    bcrypt.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app,db)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    return app