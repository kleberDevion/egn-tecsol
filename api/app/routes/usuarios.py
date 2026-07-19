from flask import Blueprint, g, jsonify, request

from app.auth import foto_url, hash_password, log_activity, require_admin, set_user_grupos, user_grupos
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("usuarios", __name__, url_prefix="/api/v1/usuarios")
bp.before_request(require_admin)

CAMPOS_EDITAVEIS = ["nome", "papel", "ativo"]


def _row_to_dict(db, row):
    d = dict(row)
    d.pop("senha_hash", None)
    d.pop("foto_path", None)
    d["foto_url"] = foto_url(row)
    d["grupos"] = user_grupos(db, row["id"])
    return d


def _get_or_404(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Usuário {usuario_id} não encontrado", 404)
    return row


def _max_admin_contas(db):
    row = db.execute("SELECT valor FROM configuracoes WHERE chave = 'max_admin_contas'").fetchone()
    return int(row["valor"]) if row else 5


def _assert_admin_slot_disponivel(db, excluir_id=None):
    filters = ["papel = 'admin'"]
    params = []
    if excluir_id is not None:
        filters.append("id != ?")
        params.append(excluir_id)
    total_admins = db.execute(
        f"SELECT COUNT(*) FROM usuarios WHERE {' AND '.join(filters)}", params
    ).fetchone()[0]
    limite = _max_admin_contas(db)
    if total_admins >= limite:
        raise ApiError("CONFLICT", f"Limite de {limite} contas de administrador atingido", 409)


@bp.get("")
def list_usuarios():
    db = get_db()
    filters, params = [], []

    if q := request.args.get("q"):
        filters.append("(nome LIKE ? OR email LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"SELECT * FROM usuarios {where} ORDER BY nome",
        f"SELECT COUNT(*) FROM usuarios {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(db, r) for r in rows], "pagination": pagination})


@bp.post("")
def create_usuario():
    body = request.get_json(force=True, silent=True) or {}
    nome, email, senha = body.get("nome"), body.get("email"), body.get("senha")
    papel = body.get("papel", "operador")
    grupos = body.get("grupos") or []
    if not nome:
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)
    if not email:
        raise ApiError("VALIDATION_ERROR", "Campo 'email' é obrigatório", 400)
    if not senha or len(senha) < 8:
        raise ApiError("VALIDATION_ERROR", "Senha deve ter ao menos 8 caracteres", 400)
    if papel not in ("admin", "operador"):
        raise ApiError("VALIDATION_ERROR", "Campo 'papel' deve ser 'admin' ou 'operador'", 400)
    if not isinstance(grupos, list) or not all(isinstance(g, str) for g in grupos):
        raise ApiError("VALIDATION_ERROR", "Campo 'grupos' deve ser uma lista de strings", 400)

    db = get_db()
    if papel == "admin":
        _assert_admin_slot_disponivel(db)

    cur = db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, papel) VALUES (?, ?, ?, ?)",
        (nome, email, hash_password(senha), papel),
    )
    set_user_grupos(db, cur.lastrowid, grupos)
    db.commit()
    log_activity(db, "create", "usuarios", cur.lastrowid, f"Usuário {nome} ({papel}) criado")
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_row_to_dict(db, row)), 201


@bp.patch("/<int:usuario_id>")
def update_usuario(usuario_id):
    db = get_db()
    _get_or_404(db, usuario_id)
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}
    grupos = body.get("grupos")

    if "papel" in updates and updates["papel"] not in ("admin", "operador"):
        raise ApiError("VALIDATION_ERROR", "Campo 'papel' deve ser 'admin' ou 'operador'", 400)
    if grupos is not None and (not isinstance(grupos, list) or not all(isinstance(g, str) for g in grupos)):
        raise ApiError("VALIDATION_ERROR", "Campo 'grupos' deve ser uma lista de strings", 400)

    perdendo_admin = usuario_id == g.user["id"] and (
        updates.get("papel") == "operador" or updates.get("ativo") == 0
    )
    if perdendo_admin:
        raise ApiError("VALIDATION_ERROR", "Não é possível remover seu próprio acesso de administrador", 400)

    if updates.get("papel") == "admin":
        _assert_admin_slot_disponivel(db, excluir_id=usuario_id)

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), usuario_id]
        db.execute(
            f"UPDATE usuarios SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )

    if grupos is not None:
        set_user_grupos(db, usuario_id, grupos)

    if updates or grupos is not None:
        db.commit()
        log_activity(db, "update", "usuarios", usuario_id, f"Usuário #{usuario_id} atualizado")

    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return jsonify(_row_to_dict(db, row))
