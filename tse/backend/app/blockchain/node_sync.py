import os
import requests
import json
from .chain import Blockchain
from .block import Block

# configuracion de nodos
# los tres nodos corren como procesos Flask independientes
# en docker-compose se definen como servicios separados
# el nodo actual se identifica por la variable de entorno
# node_id(1, 2, 3)

NODOS = {
    1: os.getenv('NODO_1_URL', 'http://tse_nodo:5000'),
    2: os.getenv('NODO_2_URL', 'http://tse_nodo:5002'),
    3: os.getenv('NODO_3_URL', 'http://tse_nodo:5003'),
}

NODO_ACTUAL = int(os.getenv('NODE_ID', '1'))

#timeout en 5 para peticiones entre nodos

TIMEOUT = 5

def _nodos_remotos() ->list[str]:
    #devuelve las URL de los nodos distintos al actual
    return [
        url for node_id, url in NODOS.items()
        if node_id != NODO_ACTUAL
    ]

# bloques nuevos

def programar(block: Block) -> dict:
    #envia unh bloque nuevo a todos los nodos remotos
    #se llama desde vote_service.py despues de agregar el bloque a la cadena local
    # patron observer: es uno de los tres observadores que vote_service dispara al emitir un voto
    #args:
    #   block: el bloque recien creado
    # retorna: 
    #   Diccionario con el resultado por nodo:
    #   {"http://nodo2:5002": "ok" | "error"}

    resultados = {}
    block_data = block.to_dict()

    for url in _nodos_remotos():
        try:
            response = requests.post(
                f"{url}/blockchain/recibir_bloque",
                json={
                    'eleccion_id': block.transactions[0].get('election_id')
                                   if block.transactions else 0,
                    'block'      : block_data
                },
                timeout=TIMEOUT
            )
 
            if response.status_code == 200:
                resultados[url] = 'ok'
            else:
                resultados[url] = f"error HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            resultados[url] = 'error: nodo no disponible'
        except requests.exceptions.Timeout:
            resultados[url] = 'error: timeout'
        except Exception as e:
            resultados[url] = f"error: {str(e)}"
    return resultados


#recepcion de bloques de otros nodos

def recibir_bloque(eleccion_id: int, block_data: dict) -> tuple[bool, str]:
    #procesa un bloque recibido por otro nodo
    #se llama desde la ruta Flask /blockchain/recibir_bloque
    #validaciones antes de aceptar el bloque:
    #   1-El block_hash del bloque recibido coinide con el hash recalculado (integridad del bloque)
    #   2-El previous_hash coincide con el hash del ultimo bloque de cadena local 
    #   3-El block_index es el siguiente esperado
    #   si todas pasan -> agrega el bloque a la cadena local
    #   si alguna falla -> rechaza y solicita sincronizacion completa
    #   retorna:
    #       (True, "ok") si el bloque fue aceptado
    #       (False, "motivo") si fue rechazado

    blockchain = Blockchain.get_instance(eleccion_id)
    bloque = Block.from_dict((block_data))

    #validacion 1: integridad del bloque recibido
    if bloque.hash != bloque.recalculate_hash():
        return False, "hash del bloque invalido"
    
    ultimo = blockchain.ultimo_bloque

    #Validacion 2: encadenamiento correcto
    if bloque.previous_hash != ultimo.hash:
        #la cadena local puede estar desactualizada
        #solicita cadena completa al nodo anterior
        print(
            f"[NodeSync] Bloque {bloque.index} rechazado"
            f"previous_hash no coincide, solicitando sincronizacion"
        )
        return False, "previous_hash no coincide -- se requiere sincronizacion"
    
    #validacion 3: indice correcto
    if bloque.index != ultimo.index + 1:
        return False, f"indice esperado {ultimo.index + 1}, recibido {bloque.index}"
    
    #todas las validaciones pasan ->agregar a la cadena local
    with blockchain._write_lock:
        blockchain.chain.append(bloque)
        blockchain._escribir(blockchain.chain)

    print(
        f"[NodeSync] Bloque {bloque.index} aceptado"
        f"Cadena local: {len(blockchain.chain)} bloques"
    )
    return True, "ok"

# sincronizacion entre nodos
def sincronizar(eleccion_id: int) -> bool:
    #solicita  la cadena  completa a todos los nodos remotos y reemplaza la cadena local si algun nodo tiene
    # una cadena mas larga y valida
    # se llama: 
    #   - al iniciar un nodo que estuvo caido
    #   - cuando recibir_bloque detecta un desencadenamiento
    #   - periodicamente  como medida de consistencia
    # implementa la regla de consenso: la cadena mas larga valida entre todos los nodos es la cadena correcta
    # retorna:
    #   True si la cadena  fue reemplada, False si ya estaba actualizada
    
    blockchain = Blockchain.get_instance(eleccion_id)
    reemplazada = False

    for url in _nodos_remotos():
        try:
            response = requests.get(
                f"{url}/blockchain/cadena/{eleccion_id}",
                timeout=TIMEOUT
            )
 
            if response.status_code != 200:
                continue
 
            data         = response.json()
            cadena_remota = data.get('chain', [])
 
            if blockchain.reemplazar_cadena(cadena_remota):
                print(
                    f"[NodeSync] Cadena de elección {eleccion_id} "
                    f"sincronizada desde {url}. "
                    f"Longitud: {len(cadena_remota)} bloques."
                )
                reemplazada = True
 
        except requests.exceptions.ConnectionError:
            print(f"[NodeSync] Nodo {url} no disponible para sincronización.")
        except requests.exceptions.Timeout:
            print(f"[NodeSync] Timeout al sincronizar con {url}.")
        except Exception as e:
            print(f"[NodeSync] Error sincronizando con {url}: {e}")
 
    return reemplazada

def obtener_cadena(eleccion_id: int) -> dict:
    
    # devuelve la cadena completa de este nodo para compartirla con otros nodos que lo soliciten.
    # se llama desde la ruta Flask GET /blockchain/cadena/<id>.
 
    # retorna:
    #     { "chain": [...], "longitud": N, "nodo": NODE_ID }
    
    blockchain = Blockchain.get_instance(eleccion_id)
    return {
        'chain'   : blockchain.get_all_blocks(),
        'longitud': blockchain.longitud,
        'nodo'    : NODO_ACTUAL,
        'valida'  : blockchain.is_valid()
    }

# estado de los nodos
def estado_nodos() -> dict:
    """
    Consulta el estado de todos los nodos remotos.
    Usado en el panel de auditoría para mostrar
    cuántos nodos están activos y sincronizados.
 
    Returns:
        {
          1: { "activo": True,  "longitud": 45 },
          2: { "activo": False, "longitud": None },
          3: { "activo": True,  "longitud": 45 }
        }
    """
    estado = {NODO_ACTUAL: {"activo": True, "nodo_actual": True}}
 
    for node_id, url in NODOS.items():
        if node_id == NODO_ACTUAL:
            continue
        try:
            response = requests.get(
                f"{url}/blockchain/health",
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                estado[node_id] = {
                    "activo"  : True,
                    "longitud": data.get('longitud'),
                    "url"     : url
                }
            else:
                estado[node_id] = {"activo": False, "url": url}
 
        except Exception:
            estado[node_id] = {"activo": False, "url": url}
 
    return estado
 