import hashlib
import json
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey
)

from ecdsa import SECP256k1, SigningKey, VerifyingKey, BadSignatureError

# Par de claves RSA por eleccion

def generar_par_claves_eleccion()-> tuple[str, str]:
    #genera un par de claves RSA 2048 bits para una eleccion
    # se llama una sola vez al crear la eleccion en elections.py
    # retorna: (clave_publica_pem, clave_privada_pem) como strings PEM
    # clave publica se usa para cifrar cada voto al emitirlo
    # clave privada se usa para descifrar al cerrar la eleccion
    # y calcular el conteo, este se guarda en elecciones.clave_privada_pem
    # la clave privada se guarda en DB
    clave_privada = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    privada_pem = clave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    publica_pem = clave_privada.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return publica_pem, privada_pem

def cargar_clave_publica(pem:str)-> RSAPublicKey:
    #carga la clave publica desde string PEM
    return serialization.load_pem_public_key(pem.encode('utf-8'))

def cargar_clave_privada(pem:str)-> RSAPrivateKey:
    #carga la clave privada desde string PEM
    return serialization.load_pem_private_key(
        pem.encode('utf-8'),
        password=None
    )


#cifrado y descifrado de votos (RSA-OAEP)
class VoteCipher:
    # Padron strategy para el cifrado de votos
    # el algoritmo es RSA-OAEP co SHA-256
    # OAEP agrega una aleatoriedad al cifrado, por lo que dos votos identicos al mismo candidatos producen cifrados distintos
    # asi se impide ataques de correlacion
    # uso
    # cipher = VoterCipher()
    # encrypted = cipher.encrypt(candidato_id, clave_publica) 
    # candidato_id = cipher.decrypt(encrypted, clave_privada)
    
    def encrypt(self, candidato_id:int, clave_publica: RSAPublicKey)->str:
        # cifra el id del candidatos con la clave publica de la eleccion
        # args: 
        #     candidato_id: ID del candidato seleccionado (entero)
        #     clave_publica: clave publica con RSA de la eleccion 
        #     returns: 
        #         voto cifrado como string hexadecimal.
        #         string va dentro de la transaccion en el chain.json
        
        voto_bytes = str(candidato_id).encode('utf-8')
        
        cifrado = clave_publica.encrypt(
            voto_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return cifrado.hex()
    
    def decrypt(self, encrypted_hex:str, clave_privada: RSAPrivateKey) -> int:
        # descrifra un voto con la clave privada de la eleccion
        # solo se llama al cerrar la eleccion para el conteo 
        # args: 
        #     encrypted_hex: voto cifrado en hexadecimal
        #     clave_privada: clave privada RSA de la elección
            
        #     returns: 
        #         candidato_id como entero:
        cifrado_bytes = bytes.fromhex(encrypted_hex)
        
        descrifrado = clave_privada.decrypt(
            cifrado_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return int(descrifrado.decode('utf-8'))
    
    
    def encrypt_blanco_nulo(self,tipo:str,clave_publica:RSAPublicKey)->str:
        #cifra el boto blanco o nulo
        # ipo debe ser blanco o nulo
        # se usa candidato_id = 0 para blancos, -1 para nulos
        
        codigos = {'BLANCO': 0, 'NULO': -1}
        return self.encrypt(codigos.get(tipo, 0), clave_publica)
    
    
    #firma digital ECDSA por transaccion
    class TransactionSigner:
        #firma por cada transaccion de voto con ECDSA sobre la curva
        # secp256k1 (igual que un Bitcoin)
        # la firma garantiza que la transaccion no fue alterada
        # despues de ser emitida, este no identifica al votante
        # la clave de firma es generada por session, no por persona
        # se genera una clase por sesion de kiosco
        
        
        @staticmethod
        def generar_clave_sesion()-> tuple[str, str]:
            # genera un par de claves ECDSA para una sesion de kiosko, esta se descarta al finalizar la sesion
            # retorna (clave_privada_hex, clave_publica_hex)
            sk = SigningKey.generate(curve=SECP256k1)
            vk = sk.get_verifying_key
            return sk.to_string().hex(), vk.to_string().hex()
        
        @staticmethod
        def firmar(transaction: dict, clave_privada_hex:str)->str:
            # firma el hash SHA256 de la transaccion
            # args:
            #     transaction: dict con voter_token, encrypted_vote
            #     clave_privada_hex: clave privada ECDSA de la sesion
            # retorna firma digital como string hexadecimal
            
            sk = SigningKey.from_string(
                bytes.fromhex(clave_privada_hex),
                curve=SECP256k1
            )
            #hash determinista de la transaccion
            tx_bytes = json.dumps(
            transaction, sort_keys=True, ensure_ascii=False
            ).encode('utf-8')
            tx_hash = hashlib.sha256(tx_bytes).digest()
 
            firma = sk.sign(tx_hash)
            return firma.hex()
        
        @staticmethod
        def verificar(transaction: dict, firma_hex: str, clave_publica_hex: str) -> bool:
            #verifica que la firma de una transacción es válida
            #usado por node_sync.py al recibir bloques de otros nodos
            #retorna: 
            #   True si la firma es válida, False si fue alterada
            
            try:
                vk = VerifyingKey.from_string(
                bytes.fromhex(clave_publica_hex),
                curve=SECP256k1
                )
 
            # Reconstruir el hash de la transacción
                tx_sin_firma = {
                     k: v for k, v in transaction.items()
                     if k != 'signature'
                }
                tx_bytes = json.dumps(
                    tx_sin_firma, sort_keys=True, ensure_ascii=False
                ).encode('utf-8')
                tx_hash = hashlib.sha256(tx_bytes).digest()
 
                vk.verify(bytes.fromhex(firma_hex), tx_hash)
                return True
 
            except BadSignatureError:
              return False
 
 
 
 #token anonimo del votante
def generar_voter_token(padron_id: int) -> str:
    salt = secrets.token_hex(16)
    combinacion = f"{padron_id}:{salt}"
    return hashlib.sha256(combinacion.encode('utf-8')).hexdigest()
 
 
def generar_codigo_recibo() -> str:
    return secrets.token_hex(16)


#Verificacion biometrica 
def generar_hash_biometrico(dato_biometrico: bytes) -> str:
    return hashlib.sha256(dato_biometrico).hexdigest()

