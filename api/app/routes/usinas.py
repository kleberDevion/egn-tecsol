from flask import Blueprint, jsonify, request

from app.auth import log_activity, require_login
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("usinas", __name__, url_prefix="/api/v1/usinas")
bp.before_request(require_login)

CAMPOS_EDITAVEIS = [
    "nome",
    "cliente_id",
    "potencia_kwp",
    "data_instalacao",
    "total_investido",
    "geracao_anual_esperada",
    "cep",
    "latitude",
    "longitude",
]


def _row_to_dict(row):
    return dict(row)


def _get_or_404(db, usina_id):
    row = db.execute("SELECT * FROM usinas WHERE id = ?", (usina_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Usina {usina_id} não encontrada", 404)
    return row


def _assert_cliente_exists(db, cliente_id):
    if cliente_id is None:
        return
    row = db.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Cliente {cliente_id} não encontrado", 404)


def _validate_full(body):
    if not body.get("nome"):
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)
    if body.get("potencia_kwp") is None:
        raise ApiError("VALIDATION_ERROR", "Campo 'potencia_kwp' é obrigatório", 400)


@bp.get("")
def list_usinas():
    db = get_db()
    filters, params = [], []

    if cliente_id := request.args.get("cliente_id"):
        filters.append("cliente_id = ?")
        params.append(cliente_id)
    if nome := request.args.get("nome"):
        filters.append("nome LIKE ?")
        params.append(f"%{nome}%")
    if potencia_min := request.args.get("potencia_min"):
        filters.append("potencia_kwp >= ?")
        params.append(potencia_min)
    if potencia_max := request.args.get("potencia_max"):
        filters.append("potencia_kwp <= ?")
        params.append(potencia_max)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"SELECT * FROM usinas {where} ORDER BY id",
        f"SELECT COUNT(*) FROM usinas {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/<int:usina_id>")
def get_usina(usina_id):
    db = get_db()
    return jsonify(_row_to_dict(_get_or_404(db, usina_id)))


@bp.get("/<int:usina_id>/geracao")
def list_geracao_da_usina(usina_id):
    db = get_db()
    _get_or_404(db, usina_id)
    filters, params = ["usina_id = ?"], [usina_id]
    if ano := request.args.get("ano"):
        filters.append("ano = ?")
        params.append(ano)
    where = f"WHERE {' AND '.join(filters)}"
    rows, pagination = paginate_query(
        db,
        f"SELECT * FROM geracao {where} ORDER BY ano, mes",
        f"SELECT COUNT(*) FROM geracao {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.post("")
def create_usina():
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    db = get_db()
    _assert_cliente_exists(db, body.get("cliente_id"))
    cur = db.execute(
        """INSERT INTO usinas (nome, cliente_id, potencia_kwp, data_instalacao, total_investido,
                                geracao_anual_esperada, cep, latitude, longitude)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            body["nome"],
            body.get("cliente_id"),
            body["potencia_kwp"],
            body.get("data_instalacao"),
            body.get("total_investido"),
            body.get("geracao_anual_esperada"),
            body.get("cep"),
            body.get("latitude"),
            body.get("longitude"),
        ),
    )
    db.commit()
    log_activity(db, "create", "usinas", cur.lastrowid, f"Usina {body['nome']} criada")
    row = db.execute("SELECT * FROM usinas WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_row_to_dict(row)), 201


@bp.put("/<int:usina_id>")
def replace_usina(usina_id):
    db = get_db()
    _get_or_404(db, usina_id)
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    _assert_cliente_exists(db, body.get("cliente_id"))
    db.execute(
        """UPDATE usinas
           SET nome = ?, cliente_id = ?, potencia_kwp = ?, data_instalacao = ?, total_investido = ?,
               geracao_anual_esperada = ?, cep = ?, latitude = ?, longitude = ?,
               atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now')
           WHERE id = ?""",
        (
            body["nome"],
            body.get("cliente_id"),
            body["potencia_kwp"],
            body.get("data_instalacao"),
            body.get("total_investido"),
            body.get("geracao_anual_esperada"),
            body.get("cep"),
            body.get("latitude"),
            body.get("longitude"),
            usina_id,
        ),
    )
    db.commit()
    log_activity(db, "update", "usinas", usina_id, f"Usina {body['nome']} atualizada")
    row = db.execute("SELECT * FROM usinas WHERE id = ?", (usina_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.patch("/<int:usina_id>")
def update_usina(usina_id):
    db = get_db()
    _get_or_404(db, usina_id)
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}
    if "cliente_id" in updates:
        _assert_cliente_exists(db, updates["cliente_id"])

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), usina_id]
        db.execute(
            f"UPDATE usinas SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )
        db.commit()
        log_activity(db, "update", "usinas", usina_id, f"Usina #{usina_id} atualizada")

    row = db.execute("SELECT * FROM usinas WHERE id = ?", (usina_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.delete("/<int:usina_id>")
def delete_usina(usina_id):
    db = get_db()
    _get_or_404(db, usina_id)
    db.execute("DELETE FROM geracao WHERE usina_id = ?", (usina_id,))
    db.execute("DELETE FROM usinas WHERE id = ?", (usina_id,))
    db.commit()
    log_activity(db, "delete", "usinas", usina_id, f"Usina #{usina_id} excluída")
    return "", 204
