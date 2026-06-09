from app.extensions import db
from app.models.conteo import Conteo
from app.models.candidate import Candidato
from app.blockchain.chain import Blockchain
from app.blockchain.crypto import VoteCipher, cargar_clave_privada
 
class ConteoService:

    # Actualiza los conteos usando únicamente el bloque recién agregado
    @staticmethod
    def actualizar_con_bloque(eleccion_id: int, bloque, clave_privada_pem: str):

        clave_privada = cargar_clave_privada(clave_privada_pem)
        cipher = VoteCipher()

        # Procesar cada voto del bloque
        for tx in bloque.transactions:
            try:
                candidato_id = cipher.decrypt(
                    tx['encrypted_vote'],
                    clave_privada
                )

                # Determinar el tipo de voto
                if candidato_id == 0:
                    tipo, candidato_id = 'BLANCO', None
                elif candidato_id == -1:
                    tipo, candidato_id = 'NULO', None
                else:
                    tipo = 'VALIDO'

                # Buscar si ya existe un registro para este resultado
                conteo = Conteo.query.filter_by(
                    eleccion_id=eleccion_id,
                    candidato_id=candidato_id,
                    tipo=tipo
                ).first()

                # Incrementar o crear el conteo
                if conteo:
                    conteo.total_votos += 1
                else:
                    db.session.add(Conteo(
                        eleccion_id=eleccion_id,
                        candidato_id=candidato_id,
                        tipo=tipo,
                        total_votos=1
                    ))

            except Exception as e:
                print(f'[ConteoService] Error descifrando transacción: {e}')
                continue

        db.session.commit()

    # Recalcula todos los resultados desde la blockchain
    @staticmethod
    def recalcular_todo(eleccion_id: int, clave_privada_pem: str):

        blockchain = Blockchain.get_instance(eleccion_id)
        clave_privada = cargar_clave_privada(clave_privada_pem)
        cipher = VoteCipher()

        # Eliminar conteos anteriores
        Conteo.query.filter_by(eleccion_id=eleccion_id).delete()
        db.session.flush()

        conteos_temp = {}

        # Recorrer todos los bloques excepto el génesis
        for bloque in blockchain.chain[1:]:
            for tx in bloque.transactions:
                try:
                    candidato_id = cipher.decrypt(
                        tx['encrypted_vote'],
                        clave_privada
                    )

                    # Clasificar el voto
                    if candidato_id == 0:
                        key = (None, 'BLANCO')
                    elif candidato_id == -1:
                        key = (None, 'NULO')
                    else:
                        key = (candidato_id, 'VALIDO')

                    conteos_temp[key] = conteos_temp.get(key, 0) + 1

                except Exception as e:
                    print(f'[ConteoService] Error descifrando: {e}')
                    continue

        # Guardar resultados finales
        for (candidato_id, tipo), total in conteos_temp.items():
            db.session.add(Conteo(
                eleccion_id=eleccion_id,
                candidato_id=candidato_id,
                tipo=tipo,
                total_votos=total
            ))

        db.session.commit()

    # Obtiene los resultados listos para mostrar
    @staticmethod
    def resultados(eleccion_id: int) -> dict:

        conteos = Conteo.query.filter_by(eleccion_id=eleccion_id).all()

        total = sum(c.total_votos for c in conteos)
        blancos = 0
        nulos = 0
        lista = []

        for c in conteos:

            # Separar votos blancos y nulos
            if c.tipo == 'BLANCO':
                blancos += c.total_votos
                continue

            if c.tipo == 'NULO':
                nulos += c.total_votos
                continue

            candidato = Candidato.query.get(c.candidato_id)

            nombre = (
                f'{candidato.nombres} {candidato.apellido_paterno}'
                if candidato else f'Candidato {c.candidato_id}'
            )

            partido = candidato.nombre_partido if candidato else '—'

            porcentaje = round(
                (c.total_votos / total * 100) if total > 0 else 0,
                2
            )

            # Agregar información para la vista
            lista.append({
                'candidato_id': c.candidato_id,
                'nombre': nombre,
                'partido': partido,
                'sigla': candidato.sigla_partido if candidato else '—',
                'color': candidato.color_partido if candidato else '#6c757d',
                'foto': candidato.foto_candidato if candidato else None,
                'votos': c.total_votos,
                'porcentaje': porcentaje
            })

        # Ordenar por cantidad de votos
        lista.sort(key=lambda x: x['votos'], reverse=True)

        return {
            'total': total,
            'candidatos': lista,
            'blancos': blancos,
            'nulos': nulos
        }