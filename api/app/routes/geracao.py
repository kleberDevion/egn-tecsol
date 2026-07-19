from flask import Blueprint, jsonify, request

from app.auth import log_activity, require_login
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("geracao", __name__, url_prefix="/api/v1/geracao")
bp.before_request(require_login)

CAMPOS_EDITAVEIS = ["usina_id", "ano", "mes", "valor_kwh"]


def _row_to_dict(row):
    return dict(row)


def _get_or_404(db, geracao_id):
    row = db.execute("SELECT * FROM geracao WHERE id = ?", (geracao_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Registro de geração {geracao_id} não encontrado", 404)
    return row


def _assert_usina_exists(db, usina_id):
    row = db.execute("SELECT id FROM usinas WHERE id = ?", (usina_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Usina {usina_id} não encontrada", 404)


def _validate_full(body):
    if not body.get("usina_id"):
        raise ApiError("VALIDATION_ERROR", "Campo 'usina_id' é obrigatório", 400)
    if not body.get("ano"):
        raise ApiError("VALIDATION_ERROR", "Campo 'ano' é obrigatório", 400)
    mes = body.get("mes")
    if mes is None or not (1 <= int(mes) <= 12):
        raise ApiError("VALIDATION_ERROR", "Campo 'mes' deve estar entre 1 e 12", 400)
    if body.get("valor_kwh") is None:
        raise ApiError("VALIDATION_ERROR", "Campo 'valor_kwh' é obrigatório", 400)


@bp.get("")
def list_geracao():
    db = get_db()
    filters, params = [], []

    if usina_id := request.args.get("usina_id"):
        filters.append("usina_id = ?")
        params.append(usina_id)
    if ano := request.args.get("ano"):
        filters.append("ano = ?")
        params.append(ano)
    if mes := request.args.get("mes"):
        filters.append("mes = ?")
        params.append(mes)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"SELECT * FROM geracao {where} ORDER BY id",
        f"SELECT COUNT(*) FROM geracao {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/<int:geracao_id>")
def get_geracao(geracao_id):
    db = get_db()
    return jsonify(_row_to_dict(_get_or_404(db, geracao_id)))


@bp.post("")
def create_geracao():
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    db = get_db()
    _assert_usina_exists(db, body["usina_id"])
    cur = db.execute(
        "INSERT INTO geracao (usina_id, ano, mes, valor_kwh) VALUES (?, ?, ?, ?)",
        (body["usina_id"], body["ano"], body["mes"], body["valor_kwh"]),
    )
    db.commit()
    log_activity(db, "create", "geracao", cur.lastrowid, f"Geração {body['ano']}/{body['mes']} registrada")
    row = db.execute("SELECT * FROM geracao WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_row_to_dict(row)), 201


@bp.put("/<int:geracao_id>")
def replace_geracao(geracao_id):
    db = get_db()
    _get_or_404(db, geracao_id)
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    _assert_usina_exists(db, body["usina_id"])
    db.execute(
        """UPDATE geracao SET usina_id = ?, ano = ?, mes = ?, valor_kwh = ?,
               atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now')
           WHERE id = ?""",
        (body["usina_id"], body["ano"], body["mes"], body["valor_kwh"], geracao_id),
    )
    db.commit()
    log_activity(db, "update", "geracao", geracao_id, f"Geração {body['ano']}/{body['mes']} atualizada")
    row = db.execute("SELECT * FROM geracao WHERE id = ?", (geracao_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.patch("/<int:geracao_id>")
def update_geracao(geracao_id):
    db = get_db()
    _get_or_404(db, geracao_id)
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}
    if "usina_id" in updates:
        _assert_usina_exists(db, updates["usina_id"])
    if "mes" in updates and not (1 <= int(updates["mes"]) <= 12):
        raise ApiError("VALIDATION_ERROR", "Campo 'mes' deve estar entre 1 e 12", 400)

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), geracao_id]
        db.execute(
            f"UPDATE geracao SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )
        db.commit()
        log_activity(db, "update", "geracao", geracao_id, f"Geração #{geracao_id} atualizada")

    row = db.execute("SELECT * FROM geracao WHERE id = ?", (geracao_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.delete("/<int:geracao_id>")
def delete_geracao(geracao_id):
    db = get_db()
    _get_or_404(db, geracao_id)
    db.execute("DELETE FROM geracao WHERE id = ?", (geracao_id,))
    db.commit()
    log_activity(db, "delete", "geracao", geracao_id, f"Geração #{geracao_id} excluída")
    return "", 204
