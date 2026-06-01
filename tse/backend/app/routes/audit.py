from flask import Blueprint, jsonify
from app.models.audit_log import AuditLog

bp_audit = Blueprint("audit", __name__)

@bp_audit.route("/")
def listar():
    logs = AuditLog.query.all()
    return jsonify([l.accion for l in logs])