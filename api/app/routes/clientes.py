from flask import Blueprint, jsonify, request

from app.auth import log_activity, require_login
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("clientes", __name__, url_prefix="/api/v1/clientes")
bp.before_request(require_login)

TIPOS_VALIDOS = ("PF", "PJ")
CAMPOS_EDITAVEIS = ["tipo", "nome", "email", "telefone", "cpf_cnpj", "endereco", "cep"]


def _row_to_dict(row):
    return dict(row)


def _get_or_404(db, cliente_id):
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Cliente {cliente_id} não encontrado", 404)
    return row


def _validate_full(body):
    if body.get("tipo") not in TIPOS_VALIDOS:
        raise ApiError("VALIDATION_ERROR", "Campo 'tipo' deve ser 'PF' ou 'PJ'", 400)
    if not body.get("nome"):
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)


@bp.get("")
def list_clientes():
    db = get_db()
    filters, params = [], []

    if nome := request.args.get("nome"):
        filters.append("nome LIKE ?")
        params.append(f"%{nome}%")
    if tipo := request.args.get("tipo"):
        filters.append("tipo = ?")
        params.append(tipo)
    if cpf_cnpj := request.args.get("cpf_cnpj"):
        filters.append("cpf_cnpj = ?")
        params.append(cpf_cnpj)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"SELECT * FROM clientes {where} ORDER BY id",
        f"SELECT COUNT(*) FROM clientes {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/<int:cliente_id>")
def get_cliente(cliente_id):
    db = get_db()
    return jsonify(_row_to_dict(_get_or_404(db, cliente_id)))


@bp.post("")
def create_cliente():
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    db = get_db()
    cur = db.execute(
        """INSERT INTO clientes (tipo, nome, email, telefone, cpf_cnpj, endereco, cep)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            body["tipo"],
            body["nome"],
            body.get("email"),
            body.get("telefone"),
            body.get("cpf_cnpj"),
            body.get("endereco"),
            body.get("cep"),
        ),
    )
    db.commit()
    log_activity(db, "create", "clientes", cur.lastrowid, f"Cliente {body['nome']} criado")
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_row_to_dict(row)), 201


@bp.put("/<int:cliente_id>")
def replace_cliente(cliente_id):
    db = get_db()
    _get_or_404(db, cliente_id)
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    db.execute(
        """UPDATE clientes
           SET tipo = ?, nome = ?, email = ?, telefone = ?, cpf_cnpj = ?, endereco = ?, cep = ?,
               atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now')
           WHERE id = ?""",
        (
            body["tipo"],
            body["nome"],
            body.get("email"),
            body.get("telefone"),
            body.get("cpf_cnpj"),
            body.get("endereco"),
            body.get("cep"),
            cliente_id,
        ),
    )
    db.commit()
    log_activity(db, "update", "clientes", cliente_id, f"Cliente {body['nome']} atualizado")
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.patch("/<int:cliente_id>")
def update_cliente(cliente_id):
    db = get_db()
    _get_or_404(db, cliente_id)
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}
    if "tipo" in updates and updates["tipo"] not in TIPOS_VALIDOS:
        raise ApiError("VALIDATION_ERROR", "Campo 'tipo' deve ser 'PF' ou 'PJ'", 400)

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), cliente_id]
        db.execute(
            f"UPDATE clientes SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )
        db.commit()
        log_activity(db, "update", "clientes", cliente_id, f"Cliente #{cliente_id} atualizado")

    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.delete("/<int:cliente_id>")
def delete_cliente(cliente_id):
    db = get_db()
    _get_or_404(db, cliente_id)

    dependentes = db.execute(
        "SELECT COUNT(*) FROM projetos WHERE cliente_id = ?", (cliente_id,)
    ).fetchone()[0]
    dependentes += db.execute(
        "SELECT COUNT(*) FROM usinas WHERE cliente_id = ?", (cliente_id,)
    ).fetchone()[0]
    if dependentes > 0:
        raise ApiError(
            "CONFLICT",
            f"Cliente {cliente_id} possui projetos ou usinas vinculadas e não pode ser removido",
            409,
        )

    db.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    db.commit()
    log_activity(db, "delete", "clientes", cliente_id, f"Cliente #{cliente_id} excluído")
    return "", 204
