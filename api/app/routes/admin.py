from flask import Blueprint, jsonify, request

from app import presence
from app.auth import foto_url, require_admin
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")
bp.before_request(require_admin)


def _row_to_dict(row):
    return dict(row)


@bp.get("/activity")
def list_activity():
    db = get_db()
    filters, params = [], []
    if usuario_id := request.args.get("usuario_id"):
        filters.append("activity_log.usuario_id = ?")
        params.append(usuario_id)
    if acao := request.args.get("acao"):
        filters.append("activity_log.acao = ?")
        params.append(acao)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"""SELECT activity_log.*, usuarios.nome AS usuario_nome, usuarios.email AS usuario_email
            FROM activity_log LEFT JOIN usuarios ON usuarios.id = activity_log.usuario_id
            {where} ORDER BY activity_log.id DESC""",
        f"SELECT COUNT(*) FROM activity_log {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/presenca")
def presenca():
    db = get_db()
    rows = db.execute(
        "SELECT id, nome, email, papel, ativo, ultimo_login_em, foto_path FROM usuarios ORDER BY nome"
    ).fetchall()
    online_ids = presence.get_online_user_ids()
    data = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("foto_path", None)
        d["foto_url"] = foto_url(r)
        d["online"] = r["id"] in online_ids
        data.append(d)
    return jsonify({"data": data})


@bp.get("/configuracoes")
def get_configuracoes():
    db = get_db()
    row = db.execute("SELECT valor FROM configuracoes WHERE chave = 'max_admin_contas'").fetchone()
    return jsonify({"max_admin_contas": int(row["valor"]) if row else 5})


@bp.patch("/configuracoes")
def update_configuracoes():
    body = request.get_json(force=True, silent=True) or {}
    max_admin_contas = body.get("max_admin_contas")
    if not isinstance(max_admin_contas, int) or max_admin_contas < 1:
        raise ApiError("VALIDATION_ERROR", "Campo 'max_admin_contas' deve ser um inteiro >= 1", 400)

    db = get_db()
    db.execute(
        "UPDATE configuracoes SET valor = ? WHERE chave = 'max_admin_contas'",
        (str(max_admin_contas),),
    )
    db.commit()
    return jsonify({"max_admin_contas": max_admin_contas})
