from flask import Flask
from app.extensions import db
from app.models import * 
import os

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    from app.routes.padron import bp_padron
    app.register_blueprint(bp_padron,url_prefix="/padron")

    db.init_app(app)

    return app