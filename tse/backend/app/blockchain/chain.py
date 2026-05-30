import json
import os
import threading
from datetime import datetime

from .block import Block

_BASE_DIR = os.path.join(
    os.path.dirname(__file__), ### blockchain/
    '..','..','..', 'blockchain_data'
)

class Blockchain:
    #gestiona la cedena de bloques de una eleccion especifica.
    #padron singleton: una sola instancia por eleccion_id
    # persistenca: lee y escribe blockchain_data/eleccion_{id}/chain.json
    #thead-safe:  usa threading, lock para escrituras concurrentes
    
    _instancia: dict = {}
    _lock_global = threading.Lock()
    
    @classmethod
    def get_instance(cls, eleccion_id: int) -> 'Blockchain':
        # devuelve la instancia existente o crea una nueva
        # thread-safe mediante lock global
        with cls._lock_global:
            if eleccion_id not in cls._instancia:
                cls._instancia[eleccion_id] = cls(eleccion_id)
            return cls._instancia[eleccion_id]
        
    @classmethod
    def limpiar_instancia(cls, eleccion_id:int):
        # elimina la instancia en memoria
        # solo  util para pruebas
        with cls._lock_global:
            cls._instancia.pop(eleccion_id,None)
            
    ## inicializacion
    
    def __init__(self, eleccion_id: int):
        self.eleccion_id = eleccion_id
        self._write_lock = threading.Lock()
        self.filepath = self._build_filepath(eleccion_id)
        self.chain: list[Block] = self._cargar_o_crear()
    
    def _build_filepath(self, eleccion_id: int) -> str:
        directorio = os.path.join(
            _BASE_DIR,
            f'eleccion_{eleccion_id:03d}'   
        )
        os.makedirs(directorio, exist_ok=True)
        return os.path.join(directorio, 'chain.json')
    
    def _cargar_o_crear(self)->list:
        # si chain.json existe ->carga la cadena desde el disco
        # si no existe -> crear el bloque generis y escribe
        
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utd-8') as f:
                    data = json.load(f)
                chain = [Block.from_dict(b) for b in data]
                print(
                    f"[Blockchain] Eleccion {self.eleccion_id}"
                    f"{len(chain)} bloques cargados desde disco"
                )
                return chain
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[Blockchain] Error al cargar chain.json: {e}")
                raise RuntimeError(
                    f"chain.json de elecion {self.eleccion_id}"
                    f"esta corrupto: {e}"
                )
        else: 
            genesis = self._crear_genesis()
            self._escribir([genesis])
            print(
                f"[Blockchain] Eleccion {self.eleccion_id}"
                f"Bloque genesis Creado"
            )
            return [genesis]
        
    def _crear_genesis(self) -> Block:
        return Block(
            index=0,
            transactions=[],
            previous_hash='0'*64,
            nonce=0
        )
        
    ### propiedades
    @property
    def ultimo_bloque(self) -> Block:
        return self.chain[-1]
    
    @property
    def longitud(self) -> int:
        return len(self.chain)
    
    
    ## agregar votos
    def add_votes(self, transacctions:dict) -> Block:
        # crea un nuevo bloque con la transaccion del votos y lo agrega a la cadena. Escribe inmediatamente a disco
        # la transaccion viene de vote_service.py y contiene:
        # {
        #     "voter_token"   : hash anónimo (no la CI),
        #     "encrypted_vote": voto cifrado con RSA,
        #     "election_id"   : id de la elección,
        #     "receipt"       : código de recibo del votante,
        #     "signature"     : firma ECDSA de la transacción
        # }
        # thread - safe: usar _write_lock para evitar escritura simultaneas que corrompan chain.json
        
        with self._write_lock:
            nuevo = Block(
                index=len(self.chain),
                transactions=[transacctions],
                previous_hash=self.ultimo_bloque.hash
            )
            self.chain.append(nuevo)
            self._escribir(self.chain)
            return nuevo
        
        ##persistencia
        
    def _escribir(self, chain:list):
        # escribe la cadena completa de chain.json
        # usa ident = 2 para que el archivo sea legible y auditable po cualquier persona
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(
                [b.to_dict() for b in chain],
                f,
                indent=2,
                ensure_ascii=False
            )
    #validacion de integridad
    def is_valid(self) -> bool:
        #verifica la integridad completa de la cadena
        # para cada bloque menos genesis comprueba:
        # 1 el hash almacenado conicide con el recalculdado
        #   -> detecata si el contenido del bloque fue alterado
        # 2 el previous_hash coincide co el hash del bloque anterior
        #   -> detecta si se inserto o elimino un bloque
        # si cualquier verificacion falla, la cadena esta comprometida
        
        for i in range(1, len(self.chain)):
            bloque_actual = self.chain[i]
            bloque_anterior = self.chain[i-1]
            
            # verificar integridad del bloque actual
            
            if bloque_actual.hash != bloque_actual.recalculate_hash():
                print(
                    f"[Blockchain] Bloque {i} comprometido"
                    f"hash no coincide"
                )
                return False
            
            if bloque_actual.previous_hash != bloque_anterior.hash:
                print(
                    f"[Blockchain] bloque {i} desconectado"
                    f"previous_hash no coincide con hash del bloque {i-1}"
                )
                return False
        return True
    
    def get_all_blocks(self) -> list:
        # devuelve todos los bloques como lista de dicts
        return [b.to_dict() for b in self.chain]
    
    def find_block_by_hash(self, block_hash:str) -> dict | None:
        # buca un bloque por su hash, para auditoria
        for bloque in self.chain:
            if bloque.hash == block_hash:
                return bloque.to_dict()
        return None
    
    def find_block_by_receipt(self, codigo_recibo:str) -> dict | None:
        # bosca el bloque que contierne una transaccion con el codigo de recibo dado. Se usa en verify_reciept.html
        
        for bloque in self.chain:
            for tx in bloque.transactions:
                if tx.get('receipt') == codigo_recibo:
                    return bloque.to_dict()
        return None
    
    def get_transactions(self) -> list:
        #devuelve todas las trasacciones de todos los bloques
        # se usa por conteo_service.py para descrifrar y contar
        
        txs = []
        for bloque in self.chain[1:]:
            txs.extend(bloque.transactions)
        return txs
    
    ### sincronizacion de nodos
    def reemplazar_cadena(self, nueva_cadena:list) -> bool:
        # reemplaza la cadena local si la nueva es mas larga y valida, se usa por node_sync.py al recibir la cadena completa de otro nodo
        # regla de consenso: la cadena mas larga valida es la que gana
        
        if len (nueva_cadena) <= len(self.chain):
            return False
        
        bloques = [Block.from_dict(b) for b in nueva_cadena]
        
        #validar integridad de la cadena recibida
        cadena_temp = Blockchain.__new__(Blockchain)
        cadena_temp.chain = bloques
        cadena_temp.eleccion_id = self.eleccion_id
        
        if not cadena_temp.is_valid():
            print(
                f"[Blockchain] Cadena recibida invalida. Se rechaza"
            )
            return False
        
        with self._write_lock:
            self.chain = bloques
            self._escribir(self.chain)
            
            print(
                f"[Blockchain] Cadena reemplazada"
                f"Nueva longitud: {len(self.chain)} bloques"
            )
            return True
        
    def __repr__(self) -> str:
        return (
            f"Blockchain(eleccion={self.eleccion_id}), "
            f"bloques={self.chain}, "
            f"valida={self.is_valid()}"
        )