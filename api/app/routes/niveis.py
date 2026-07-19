from flask import Blueprint, jsonify, request

from app.auth import require_admin
from app.db import get_db
from app.errors import ApiError

bp = Blueprint("niveis", __name__, url_prefix="/api/v1/niveis")

# Leitura pública (sem login): tanto o CRM quanto o app de indicações
# precisam mostrar a tabela de níveis/comissão, e ela não tem dado sensível.

CAMPOS_EDITAVEIS = ("label", "valor_fixo", "percentual")


@bp.get("")
def list_niveis():
    db = get_db()
    rows = db.execute("SELECT * FROM niveis_config ORDER BY ordem").fetchall()
    return jsonify({"data": [dict(r) for r in rows]})


@bp.patch("/<nivel>")
def update_nivel(nivel):
    require_admin()
    db = get_db()
    existente = db.execute("SELECT 1 FROM niveis_config WHERE nivel = ?", (nivel,)).fetchone()
    if existente is None:
        raise ApiError("NOT_FOUND", f"Nível '{nivel}' não encontrado", 404)

    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}
    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE niveis_config SET {set_clause} WHERE nivel = ?", [*updates.values(), nivel])
        db.commit()

    row = db.execute("SELECT * FROM niveis_config WHERE nivel = ?", (nivel,)).fetchone()
    return jsonify(dict(row))
