from flask import Flask,jsonify
from config import Config
from models import db,Ciudadano
from auth import require_api_key

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

@app.route("/ciudadanos",methods=['GET'])
@require_api_key
def get_ciudadanos():
    ciudadanos = Ciudadano.query.filter(Ciudadano.activo==True).all()
    resultado = []
    for ciudadano in ciudadanos:
        resultado.append({
            "ci":ciudadano.ci,
            "nombres":ciudadano.nombres,
            "apellido_paterno":ciudadano.apellido_paterno,
            "apellido_materno":ciudadano.apellido_materno
            })

    return jsonify(resultado),200

if __name__ == "__main__":
    app.run(port=5001, debug=True)
    