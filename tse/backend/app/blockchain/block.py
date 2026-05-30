import hashlib
import json
from datetime import datetime

class Block():

    def __init__(self, index: int, transactions: list, previous_hash: str, nonce: int = 0):
        # posicion del bloque dentro de la cadena
        self.index = index
        
        # Fecha y hora de creacion en formato UTC (tiempo universal coordinado)
        self.timestamp = datetime.utcnow().isoformat()
        
        # lista de transacciones almacenadas en el bloque
        self.transactions = transactions
        
        # hash del bloque anterior
        self.previous_hash = previous_hash
        
        #valor utilizado para validaciones
        self.nonce = nonce
        
        #calcular raiz de Merkle
        self.merkle_root    = self._calculate_merkle_root()
        
        #generar el hash unico del bloque
        self.hash = self._calculate_hash()
        
    #calculo del hash - genera el hash SHA-256 del bloque
    def _calculate_hash(self) -> str:
        
        #serializa la informacion del bloque
        block_data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce
        }, sort_keys=True, ensure_ascii=False)
        
        #aplicar SHA-256 y devolver el resultado
        
        return hashlib.sha256(
            block_data.encode('utf-8')
        ).hexdigest()
        
        
    # recalcula el hash para verificar integridad
    
    def recalculate_hash(self) -> str:
        return self._calculate_hash()
    
    # Construccion de la raiz Merkle
    def _calculate_merkle_root(self) -> str:
        # caso especial para bloque genesis 
        if not self.transactions:
            return hashlib.sha256(
                b'genesis'
            ).hexdigest()
            
        # generar hash individual para transaccion
        hashes = [
            hashlib.sha256(
                json.dumps(
                    tx, 
                    sort_keys=True,
                    ensure_ascii=False
                ).encode('utf-8')
            ).hexdigest()
            for tx in self.transactions
        ]
        
        # reducir el arbol hasta obtener una unica raiz
        while len(hashes) > 1:
            # si hay una cantidad impar se duplica el ultimo hash
            
            if len (hashes) % 2 == 0:
                hashes.append(hashes[-1])
                
            # combinar hashes de dos en dos
            
            hashes = [
                hashlib.sha256(
                    (hashes[i] + hashes[i+1]).encode('utf-8')
                ).hexdigest()
                for i in range(0, len(hashes),2)
            ]
            
        return hashes[0]
    
    
    
    # conversion del bloque a un diccionario 
    # se utiliza para Json y cominicacion entre nodos
    
    def to_dict(self) -> str:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "hash": self.hash
        }
       
       
    # reconstruye un bloque desde un diccionario 
    @classmethod
    def from_dict(cls, data: dict) -> 'Block':
        # crear instancia sin ejecutar el __init__
        block  = cls.__new__(cls)
        
        #restaurar atributos almacenados
        block.index = data['index']
        block.timestamp = data['timestamp']
        block.transactions = data['transactions']
        block.previous_hash = data['previous_hash']
        block.merkle_root = data['merkle_root']
        block.nonce = data['nonce']
        block.hash = data['hash']
        
        return block
    
    #representacion para depuracion
    
    def __repr__(self) -> str:
        return (
            f"Block(index={self.index}), "
            f"txs={len(self.transactions)}, "
            f"hash={self.hash[:12]}..."
        )
    