from flask import Blueprint, jsonify, request

from app.auth import require_admin
from app.db import get_db
from app.errors import ApiError

bp = Blueprint("niveis", __name__, url_prefix="/api/v1/niveis")

# Leitura pública (sem login): tanto o CRM quanto o app de indicações
# precisam mostrar a tabela de níveis/comissão, e ela não tem dado sensível.

# niveis_config hoje só serve pra progressão/labels (indicador → apoiador →
# ...). Os antigos valor_fixo/percentual saíram do cálculo — a comissão real é
# a multi-nível por kWh (tabela comissao_niveis, rotas /comissao abaixo).
CAMPOS_EDITAVEIS = ("label",)


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


# --- Comissão por kWh (modelo vigente) ------------------------------------
# nivel 1 = quem indicou o cliente; 2 = quem recrutou o nível 1; 3 = quem
# recrutou o nível 2. O sync com a Solarz lê esses valores ao fechar a venda.


@bp.get("/comissao")
def list_comissao_niveis():
    db = get_db()
    rows = db.execute("SELECT * FROM comissao_niveis ORDER BY nivel").fetchall()
    return jsonify({"data": [dict(r) for r in rows]})


@bp.patch("/comissao/<int:nivel>")
def update_comissao_nivel(nivel):
    require_admin()
    db = get_db()
    existente = db.execute("SELECT 1 FROM comissao_niveis WHERE nivel = ?", (nivel,)).fetchone()
    if existente is None:
        raise ApiError("NOT_FOUND", f"Nível de comissão {nivel} não encontrado", 404)

    body = request.get_json(force=True, silent=True) or {}
    valor = body.get("valor_por_kwh")
    if not isinstance(valor, (int, float)) or valor < 0:
        raise ApiError("VALIDATION_ERROR", "'valor_por_kwh' deve ser um número >= 0", 400)

    db.execute("UPDATE comissao_niveis SET valor_por_kwh = ? WHERE nivel = ?", (valor, nivel))
    db.commit()
    row = db.execute("SELECT * FROM comissao_niveis WHERE nivel = ?", (nivel,)).fetchone()
    return jsonify(dict(row))
