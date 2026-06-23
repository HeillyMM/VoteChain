import json
import random
import threading

from locust import HttpUser, task, between, events

BASE_URL = "http://localhost:5000" 

ADMIN_EMAIL = "admin@tse.gob.bo"
ADMIN_PASSWORD = "Admin123!"

ELECCION_ID = 1 
SESIONES_POOL_FILE = "sesiones_pool.json"  
_pool_lock = threading.Lock()
_sesiones_pool = []


@events.test_start.add_listener
def cargar_pool_sesiones(environment, **kwargs):
    global _sesiones_pool
    try:
        with open(SESIONES_POOL_FILE) as f:
            _sesiones_pool = json.load(f)
        print(f"[setup] {len(_sesiones_pool)} sesiones de votación cargadas desde {SESIONES_POOL_FILE}")
    except FileNotFoundError:
        print(f"[setup] No se encontró {SESIONES_POOL_FILE} -> la tarea 'Emisión de voto' se saltará. "
              f"Corre preparar_sesiones.py antes si quieres medirla.")
        _sesiones_pool = []


def obtener_sesion():
    with _pool_lock:
        if _sesiones_pool:
            return _sesiones_pool.pop()
    return None


class VoteChainUser(HttpUser):
    host = BASE_URL
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            name="01_Login",
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def consultar_padron(self):
        self.client.get(f"/api/elecciones/{ELECCION_ID}/padron", name="02_Consultar_Padron")

    @task(1)
    def registrar_candidato(self):
        self.client.post(
            f"/api/elecciones/{ELECCION_ID}/candidatos",
            json={
                "numero_lista": random.randint(1000, 999999),
                "sigla_partido": "TEST",
                "nombre_partido": "Partido de Prueba",
                "nombres": "Candidato",
                "apellido_paterno": "Carga",
            },
            name="03_Registrar_Candidato",
        )

    @task(2)
    def emitir_voto(self):
        sesion = obtener_sesion()
        if not sesion:
            return 

        self.client.get(f"/api/votacion/papeleta/{sesion['sesion_id']}", name="04a_Papeleta_Voto")
        self.client.post(
            "/api/votacion/emitir",
            json={
                "sesion_id": sesion["sesion_id"],
                "tipo_voto": "VALIDO",
                "candidato_id": sesion["candidato_id"],
            },
            name="04b_Emitir_Voto",
        )

    @task(3)
    def consultar_resultados(self):
        self.client.get(f"/api/resultados/{ELECCION_ID}/participacion", name="05_Consultar_Resultados")