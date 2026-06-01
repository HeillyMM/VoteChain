from flask import Flask, render_template

app = Flask(__name__)

# ==========================
# AUTENTICACIÓN
# ==========================

@app.route("/")
def login():
    return render_template("auth/login.html")

# ==========================
# ADMINISTRADOR
# ==========================

@app.route("/admin")
def admin():
    return render_template("admin/dashboard.html")

@app.route("/candidatos")
def candidatos():
    return render_template("admin/candidates.html")

@app.route("/padron")
def padron():
    return render_template("admin/padron.html")

@app.route("/Eleccion")
def Eleccion():
    return render_template("admin/election_form.html")

@app.route("/eleciones")
def eleciones():
    return render_template("admin/elections.html")

@app.route("/candidato/nuevo")
def candidato_nuevo():
    return render_template("admin/candidate_form.html")
# ==========================
# VOTANTE
# ==========================

@app.route("/votante")
def votante():
    return render_template("kiosk/ingreso.html")

@app.route("/boleta")
def boleta():
    return render_template("kiosk/ballot.html")

@app.route("/emitido")
def emitido():
    return render_template("kiosk/receipt.html")

@app.route("/verificar")
def verificar():
    return render_template("kiosk/verify.html")

# ==========================
# BLOCKCHAIN
# ==========================

@app.route("/blockchain")
def blockchain():
    return render_template("audit/chain.html")

@app.route("/auditoria")
def auditoria():
    return render_template("audit/verify_receipt.html")

# ==========================
# RESULTADOS
# ==========================

@app.route("/resultados")
def resultados():
    return render_template("results/dashboard.html")

# ==========================
# OPERADOR ELECTORAL
# ==========================

@app.route("/operador")
def operador():
    return render_template("operator/dashboard.html")

@app.route("/operador/ciudadanos")
def operador_ciudadanos():
    return render_template("operator/ciudadanos.html")

@app.route("/operador/verificar")
def operador_verificar():
    return render_template("operator/verificar.html")

@app.route("/operador/habilitados")
def operador_habilitados():
    return render_template("operator/habilitados.html")



if __name__ == "__main__":
    app.run(debug=True)