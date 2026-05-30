from flask import Flask
from tse.backend.app.extensions import db

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = ('mysql+pymysql://tse_user:tse_pass@localhost/tse_db')
    # 'mysql+pymysql://tse_user:tse_pass@mariadb/tse_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    return app