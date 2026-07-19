from flask import Blueprint, jsonify, request

from app.auth import log_activity, require_login
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("concessionarias", __name__, url_prefix="/api/v1/concessionarias")
bp.before_request(require_login)


def _row_to_dict(row):
    return dict(row)


def _get_or_404(db, concessionaria_id):
    row = db.execute("SELECT * FROM concessionarias WHERE id = ?", (concessionaria_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Concessionária {concessionaria_id} não encontrada", 404)
    return row


@bp.get("")
def list_concessionarias():
    db = get_db()
    rows, pagination = paginate_query(
        db,
        "SELECT * FROM concessionarias ORDER BY id",
        "SELECT COUNT(*) FROM concessionarias",
        [],
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/<int:concessionaria_id>")
def get_concessionaria(concessionaria_id):
    db = get_db()
    return jsonify(_row_to_dict(_get_or_404(db, concessionaria_id)))


@bp.post("")
def create_concessionaria():
    body = request.get_json(force=True, silent=True) or {}
    if not body.get("nome"):
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)
    db = get_db()
    cur = db.execute("INSERT INTO concessionarias (nome) VALUES (?)", (body["nome"],))
    db.commit()
    log_activity(db, "create", "concessionarias", cur.lastrowid, f"Concessionária {body['nome']} criada")
    row = db.execute("SELECT * FROM concessionarias WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_row_to_dict(row)), 201


@bp.put("/<int:concessionaria_id>")
@bp.patch("/<int:concessionaria_id>")
def update_concessionaria(concessionaria_id):
    db = get_db()
    _get_or_404(db, concessionaria_id)
    body = request.get_json(force=True, silent=True) or {}
    if not body.get("nome"):
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)
    db.execute(
        "UPDATE concessionarias SET nome = ?, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
        (body["nome"], concessionaria_id),
    )
    db.commit()
    log_activity(db, "update", "concessionarias", concessionaria_id, f"Concessionária {body['nome']} atualizada")
    row = db.execute("SELECT * FROM concessionarias WHERE id = ?", (concessionaria_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.delete("/<int:concessionaria_id>")
def delete_concessionaria(concessionaria_id):
    db = get_db()
    _get_or_404(db, concessionaria_id)
    db.execute("DELETE FROM concessionarias WHERE id = ?", (concessionaria_id,))
    db.commit()
    log_activity(db, "delete", "concessionarias", concessionaria_id, f"Concessionária #{concessionaria_id} excluída")
    return "", 204
