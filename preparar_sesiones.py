import json
import requests

BASE_URL = "http://localhost:5000"

OPERADOR_EMAIL = "ejemplo@gmail.com"
OPERADOR_PASSWORD = "ejemplo123"

ADMIN_EMAIL = "admin@tse.gob.bo"
ADMIN_PASSWORD = "Admin123!"

ELECCION_ID = 2
KIOSCO_IDS = [4,5,6]     
                      
NUM_SESIONES = 20     
                      

def login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def main():
    print("Iniciando sesión como operador...")
    operador_token = login(OPERADOR_EMAIL, OPERADOR_PASSWORD)
    op_headers = {"Authorization": f"Bearer {operador_token}"}

    print("Iniciando sesión como admin (para listar candidatos)...")
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print("Consultando candidatos de la elección...")
    r = requests.get(f"{BASE_URL}/api/elecciones/{ELECCION_ID}/candidatos", headers=admin_headers)
    r.raise_for_status()
    candidatos = r.json()
    if not candidatos:
        raise SystemExit("La elección no tiene candidatos. Crea candidatos antes de continuar (CU-03).")
    candidato_ids = [c["id"] for c in candidatos]

    print("Consultando padrón para obtener votantes habilitados sin votar...")
    r = requests.get(f"{BASE_URL}/api/elecciones/{ELECCION_ID}/padron", headers=op_headers)
    r.raise_for_status()
    padron = r.json()
    disponibles = [p for p in padron if p["habilitado"] and not p["ya_voto"]]

    if len(disponibles) < NUM_SESIONES:
        print(f"Solo hay {len(disponibles)} votantes disponibles; "
              f"se generarán {len(disponibles)} sesiones en vez de {NUM_SESIONES}.")

    pool = []
    for i, votante in enumerate(disponibles[:NUM_SESIONES]):
        kiosco_id = KIOSCO_IDS[i % len(KIOSCO_IDS)]
        body = {"eleccion_id": ELECCION_ID, "ci": votante["ci"], "kiosco_id": kiosco_id}
        r = requests.post(f"{BASE_URL}/api/kioscos/habilitar", json=body, headers=op_headers)
        if r.status_code != 200:
            print(f"  ✗ No se pudo habilitar CI {votante['ci']}: {r.json().get('error')}")
            continue
        sesion_id = r.json()["sesion_id"]
        candidato_id = candidato_ids[i % len(candidato_ids)]
        pool.append({"sesion_id": sesion_id, "candidato_id": candidato_id})
        print(f"  ✓ Sesión {sesion_id} creada para CI {votante['ci']} (kiosco {kiosco_id})")

    with open("sesiones_pool.json", "w") as f:
        json.dump(pool, f, indent=2)

    print(f"\n {len(pool)} sesiones guardadas en sesiones_pool.json")
    print(" Ejecuta 'locust -f locustfile.py' AHORA — las sesiones expiran en 5 minutos.")


if __name__ == "__main__":
    main()