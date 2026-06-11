from app.models.recinto import Recinto,Departamento,Kiosco
from app.models.election import Eleccion
from app.models.padron import PadronElectoral
from app.extensions import db

class RecintoService:
    
    @staticmethod
    def obtener_por_id(recinto_id):
        return Recinto.query.get(recinto_id)

    @staticmethod
    def listar_departamentos():
        return Departamento.query.all()
    
    @staticmethod
    def listar_todos_recintos():
        return Recinto.query.all()

    @staticmethod
    def listar_todos_activos():
        return Recinto.query.filter_by(activo=True).all()

    @staticmethod
    def listar_recintos_eleccion(eleccion_id):
        eleccion = Eleccion.query.get(eleccion_id)
        return eleccion.recintos
    
    @staticmethod
    def existe_recinto(codigo,nombre,direccion,municipio,departamento_id,total_mesas):
        return Recinto.query.filter_by(
            codigo=codigo,
            nombre=nombre,
            direccion=direccion,
            municipio=municipio,
            departamento_id=departamento_id,
            total_mesas=total_mesas,
        ).first()

    @staticmethod 
    def crear(
        codigo,
        nombre,
        direccion,
        municipio,
        departamento_id,
        total_mesas,
    ):
        recinto = Recinto(
            codigo=codigo,
            nombre=nombre,
            direccion=direccion,
            municipio=municipio,
            departamento_id=departamento_id,
            total_mesas=total_mesas,
        )
        
        db.session.add(recinto)
        db.session.commit()

    @staticmethod 
    def editar(
        codigo,
        nombre,
        direccion,
        municipio,
        departamento_id,
        total_mesas,
        activo,
        recinto_id
    ):
        recinto = Recinto.query.get(recinto_id)
        recinto.codigo=codigo
        recinto.nombre=nombre
        recinto.direccion=direccion
        recinto.municipio=municipio
        recinto.departamento_id=departamento_id
        recinto.total_mesas=total_mesas
        recinto.activo = activo
        db.session.commit()

    @staticmethod
    def eliminar(recinto_id):
        recinto = Recinto.query.get(recinto_id)
        kioscos = Kiosco.query.filter_by(recinto_id=recinto_id).all()
        padrones = PadronElectoral.query.filter_by(recinto_id=recinto_id)
        for kiosco in kioscos:
            db.session.delete(kiosco)
        for padron in padrones:
            padron.mesa_numero = None
        db.session.delete(recinto)
        db.session.commit()

    @staticmethod
    def recintos(eleccion_id,recintos_ids:list):
       
        eleccion = Eleccion.query.get(eleccion_id)
        for recinto_id in recintos_ids:
            recinto = Recinto.query.get(recinto_id)
            if recinto not in eleccion.recintos:
                eleccion.recintos.append(recinto)

        for recinto in eleccion.recintos[:]:
            if recinto.id not in recintos_ids:
                eleccion.recintos.remove(recinto)
        
        db.session.commit()