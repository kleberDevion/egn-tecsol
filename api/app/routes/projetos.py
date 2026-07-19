from flask import Blueprint, jsonify, request

from app.auth import log_activity, require_login
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("projetos", __name__, url_prefix="/api/v1/projetos")
bp.before_request(require_login)

CAMPOS_EDITAVEIS = ["codigo", "cliente_id", "ano", "pasta", "status"]


def _row_to_dict(row):
    return dict(row)


def _get_or_404(db, projeto_id):
    row = db.execute("SELECT * FROM projetos WHERE id = ?", (projeto_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Projeto {projeto_id} não encontrado", 404)
    return row


def _assert_cliente_exists(db, cliente_id):
    row = db.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Cliente {cliente_id} não encontrado", 404)


def _validate_full(body):
    if not body.get("codigo"):
        raise ApiError("VALIDATION_ERROR", "Campo 'codigo' é obrigatório", 400)
    if not body.get("cliente_id"):
        raise ApiError("VALIDATION_ERROR", "Campo 'cliente_id' é obrigatório", 400)
    if not body.get("ano"):
        raise ApiError("VALIDATION_ERROR", "Campo 'ano' é obrigatório", 400)


@bp.get("")
def list_projetos():
    db = get_db()
    filters, params = [], []

    if cliente_id := request.args.get("cliente_id"):
        filters.append("cliente_id = ?")
        params.append(cliente_id)
    if ano := request.args.get("ano"):
        filters.append("ano = ?")
        params.append(ano)
    if codigo := request.args.get("codigo"):
        filters.append("codigo LIKE ?")
        params.append(f"%{codigo}%")

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"SELECT * FROM projetos {where} ORDER BY id",
        f"SELECT COUNT(*) FROM projetos {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/<int:projeto_id>")
def get_projeto(projeto_id):
    db = get_db()
    return jsonify(_row_to_dict(_get_or_404(db, projeto_id)))


@bp.get("/<int:projeto_id>/documentos")
def list_documentos_do_projeto(projeto_id):
    db = get_db()
    _get_or_404(db, projeto_id)
    rows, pagination = paginate_query(
        db,
        "SELECT * FROM documentos WHERE projeto_id = ? ORDER BY id",
        "SELECT COUNT(*) FROM documentos WHERE projeto_id = ?",
        [projeto_id],
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.post("")
def create_projeto():
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    db = get_db()
    _assert_cliente_exists(db, body["cliente_id"])
    cur = db.execute(
        "INSERT INTO projetos (codigo, cliente_id, ano, pasta) VALUES (?, ?, ?, ?)",
        (body["codigo"], body["cliente_id"], body["ano"], body.get("pasta")),
    )
    db.commit()
    log_activity(db, "create", "projetos", cur.lastrowid, f"Projeto {body['codigo']} criado")
    row = db.execute("SELECT * FROM projetos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_row_to_dict(row)), 201


@bp.put("/<int:projeto_id>")
def replace_projeto(projeto_id):
    db = get_db()
    _get_or_404(db, projeto_id)
    body = request.get_json(force=True, silent=True) or {}
    _validate_full(body)
    _assert_cliente_exists(db, body["cliente_id"])
    db.execute(
        """UPDATE projetos SET codigo = ?, cliente_id = ?, ano = ?, pasta = ?,
               atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now')
           WHERE id = ?""",
        (body["codigo"], body["cliente_id"], body["ano"], body.get("pasta"), projeto_id),
    )
    db.commit()
    log_activity(db, "update", "projetos", projeto_id, f"Projeto {body['codigo']} atualizado")
    row = db.execute("SELECT * FROM projetos WHERE id = ?", (projeto_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.patch("/<int:projeto_id>")
def update_projeto(projeto_id):
    db = get_db()
    _get_or_404(db, projeto_id)
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}
    if "cliente_id" in updates:
        _assert_cliente_exists(db, updates["cliente_id"])

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), projeto_id]
        db.execute(
            f"UPDATE projetos SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )
        db.commit()
        log_activity(db, "update", "projetos", projeto_id, f"Projeto #{projeto_id} atualizado")

    row = db.execute("SELECT * FROM projetos WHERE id = ?", (projeto_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.delete("/<int:projeto_id>")
def delete_projeto(projeto_id):
    db = get_db()
    _get_or_404(db, projeto_id)
    db.execute("DELETE FROM documentos WHERE projeto_id = ?", (projeto_id,))
    db.execute("DELETE FROM projetos WHERE id = ?", (projeto_id,))
    db.commit()
    log_activity(db, "delete", "projetos", projeto_id, f"Projeto #{projeto_id} excluído")
    return "", 204
