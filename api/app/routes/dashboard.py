from flask import Blueprint, g, jsonify

from app.auth import require_login
from app.db import get_db
from app.pagination import paginate_query

bp = Blueprint("dashboard", __name__, url_prefix="/api/v1/dashboard")
bp.before_request(require_login)


def _row_to_dict(row):
    return dict(row)


@bp.get("/minhas-metricas")
def minhas_metricas():
    db = get_db()
    rows = db.execute(
        "SELECT acao, COUNT(*) AS total FROM activity_log WHERE usuario_id = ? GROUP BY acao",
        (g.user["id"],),
    ).fetchall()
    por_acao = {r["acao"]: r["total"] for r in rows}
    return jsonify(
        {
            "total_acoes": sum(por_acao.values()),
            "criacoes": por_acao.get("create", 0),
            "edicoes": por_acao.get("update", 0),
            "exclusoes": por_acao.get("delete", 0),
            "logins": por_acao.get("login", 0),
            "ultimo_login_em": g.user["ultimo_login_em"],
        }
    )


@bp.get("/minha-atividade")
def minha_atividade():
    db = get_db()
    rows, pagination = paginate_query(
        db,
        "SELECT * FROM activity_log WHERE usuario_id = ? ORDER BY id DESC",
        "SELECT COUNT(*) FROM activity_log WHERE usuario_id = ?",
        [g.user["id"]],
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/avaliacoes-suporte")
def avaliacoes_suporte():
    """Agregado do quão bem o suporte interno tem sido avaliado — nunca expõe
    quem fez cada avaliação (operador) nem quebra por admin individual."""
    db = get_db()
    row = db.execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN positiva = 1 THEN 1 ELSE 0 END) AS positivas,
                  SUM(CASE WHEN positiva = 0 THEN 1 ELSE 0 END) AS negativas
           FROM suporte_avaliacoes"""
    ).fetchone()
    return jsonify(
        {
            "total": row["total"] or 0,
            "positivas": row["positivas"] or 0,
            "negativas": row["negativas"] or 0,
        }
    )
