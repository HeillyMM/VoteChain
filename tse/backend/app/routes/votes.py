# votes.py — rutas del proceso de votación

# Permite:
# - Mostrar la boleta al votante.
# - Registrar el voto.
# - Mostrar el recibo de votación.
# - Mostrar una pantalla de acceso denegado.

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)

from app.services.vote_service import VoteService
from app.services.candidato_service import CandidatoService
from app.services.election_service import EleccionService

bp_votes = Blueprint('bp_votes', __name__, url_prefix='/votar')


# Muestra la boleta de votación
@bp_votes.route('/', methods=['GET'])
def ballot():

    token = request.args.get('token')

    if not token:
        flash('Acceso no autorizado. Solicite habilitación al operador.', 'danger')
        return redirect(url_for('bp_votes.acceso_denegado'))

    # Verificar que la sesión de votación sea válida
    validacion = VoteService.validar_token(token)

    if not validacion['ok']:
        flash(validacion['error'], 'danger')
        return redirect(url_for('bp_votes.acceso_denegado'))

    sesion = validacion['sesion']

    # Obtener la elección actualmente habilitada
    eleccion = EleccionService.get_activa()

    if not eleccion:
        flash('No hay una elección activa en este momento.', 'danger')
        return redirect(url_for('bp_votes.acceso_denegado'))

    # Cargar candidatos disponibles
    candidatos = CandidatoService.listar(eleccion.id)

    return render_template(
        'voter/ballot.html',
        token=token,
        candidatos=candidatos,
        eleccion=eleccion,
        operador=sesion.operador,
        sesion=sesion
    )


# Procesa el voto enviado desde la boleta
@bp_votes.route('/', methods=['POST'])
def emitir():

    token = request.form.get('token')
    candidato_id = request.form.get('candidato_id', type=int)
    eleccion_id = request.form.get('eleccion_id', type=int)

    if not token or not candidato_id or not eleccion_id:
        flash('Datos incompletos. Vuelva a intentarlo.', 'danger')
        return redirect(url_for('bp_votes.acceso_denegado'))

    resultado = VoteService.emitir_voto(
        token=token,
        candidato_id=candidato_id,
        eleccion_id=eleccion_id
    )

    if not resultado['ok']:
        flash(resultado['error'], 'danger')
        return redirect(url_for('bp_votes.acceso_denegado'))

    # Guardar temporalmente los datos del recibo
    session['recibo_data'] = {
        'block_hash': resultado['block_hash'],
        'block_index': resultado['block_index'],
        'codigo_recibo': resultado['codigo_recibo']
    }

    return redirect(url_for('bp_votes.recibo'))


# Muestra el comprobante de votación
@bp_votes.route('/recibo', methods=['GET'])
def recibo():

    # Recuperar y eliminar los datos guardados en sesión
    recibo_data = session.pop('recibo_data', None)

    if not recibo_data:
        flash('No hay datos de recibo disponibles.', 'warning')
        return redirect(url_for('bp_votes.acceso_denegado'))

    return render_template(
        'voter/receipt.html',
        recibo=recibo_data
    )


# Pantalla de error para accesos no válidos
@bp_votes.route('/acceso-denegado')
def acceso_denegado():

    return render_template(
        'voter/ballot.html',
        error=True
    ), 403