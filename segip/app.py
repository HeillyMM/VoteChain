from flask import Flask
from config import Config
from models import db

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

@app.route("/")
def home():
    return {"mensaje": "SEGIP funcionando"}

if __name__ == "__main__":
    app.run(port=5001, debug=True)
    