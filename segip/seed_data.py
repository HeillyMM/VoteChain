# seed --> llenado de datos en la base de datos (ejecutar para llenar base de datos)

from datetime import date
import random
from app import app
from models import db, Departamento, Ciudadano, Biometria

nombres = ["Juan", "Maria", "Carlos", "Ana", "Luis", "Sofia", "Miguel", "Lucia"]
apellidos = ["Perez", "Gomez", "Flores", "Mamani", "Quispe", "Rojas", "Lopez", "Torrez"]
departamentos_ids = list(range(1, 10)) 

def run_seed():
    with app.app_context():

        print("Limpiando datos...")
        Biometria.query.delete()
        Ciudadano.query.delete()
        db.session.commit()
        print("Insertando ciudadanos...")

        for i in range(1, 51):
            ci = str(1000000 + i)
            ciudadano = Ciudadano(
                ci=ci,
                complemento="",
                nombres=random.choice(nombres),
                apellido_paterno=random.choice(apellidos),
                apellido_materno=random.choice(apellidos),
                fecha_nacimiento=date(1990, random.randint(1, 12), random.randint(1, 28)),
                lugar_nacimiento="Bolivia",
                sexo=random.choice(["M", "F"]),
                estado_civil=random.choice(["SOLTERO", "CASADO", "DIVORCIADO"]),
                departamento_id=random.choice(departamentos_ids),
                municipio="Municipio " + str(random.randint(1, 20)),
                domicilio="Zona " + str(random.randint(1, 50)),
                vivo=True,
                activo=True
            )

            db.session.add(ciudadano)
            db.session.flush()
            bio = Biometria(
                ciudadano_id=ciudadano.id,
                foto_hash=f"foto_{ci}",
                huella_hash=f"huella_{ci}"
            )

            db.session.add(bio)

        db.session.commit()
        print("Seed completado ✔")

if __name__ == "__main__":
    run_seed()