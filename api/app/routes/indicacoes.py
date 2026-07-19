from flask import Blueprint, g, jsonify, request

from app.auth import log_activity, require_login
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query
from app.socket import broadcast_mensagem

bp = Blueprint("indicacoes", __name__, url_prefix="/api/v1/indicacoes")
bp.before_request(require_login)

STATUS_VALIDOS = ("recebido", "em_atendimento", "negociacao", "fechado", "perdido", "cancelado")
RESULTADOS_VALIDOS = ("novo_contrato", "em_andamento", "sem_interesse", "cancelado")
CAMPOS_EDITAVEIS = ["status", "setor", "valor_sistema", "resultado", "tipo_contrato", "observacoes"]

# Níveis de comissão: nunca aceitos do corpo da requisição, sempre lidos daqui.
NIVEL_ORDEM = ["indicador", "apoiador", "parceiro", "embaixador", "elite"]


def _row_to_dict(row):
    return dict(row)


def _get_or_404(db, indicacao_id):
    row = db.execute("SELECT * FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Indicação {indicacao_id} não encontrada", 404)
    return row


def _proximo_nivel(nivel_atual, total_vendas):
    if total_vendas >= 10:
        return "elite"
    if total_vendas >= 5 and nivel_atual == "indicador":
        return "parceiro"
    if total_vendas >= 5 and nivel_atual == "apoiador":
        return "embaixador"
    if total_vendas >= 3 and nivel_atual == "indicador":
        return "apoiador"
    if total_vendas >= 3 and nivel_atual == "apoiador":
        return "parceiro"
    return nivel_atual


def _fechar_indicacao(db, indicacao, valor_sistema):
    """Calcula a comissão a partir de niveis_config e atualiza os totais/nível do
    indicador. Espelha o trigger `handle_indicacao_fechada` do app original."""
    indicador = db.execute(
        "SELECT * FROM indicadores WHERE id = ?", (indicacao["indicador_id"],)
    ).fetchone()
    nivel = db.execute(
        "SELECT * FROM niveis_config WHERE nivel = ?", (indicador["nivel"],)
    ).fetchone()
    valor = valor_sistema or 0
    comissao = nivel["valor_fixo"] + valor * nivel["percentual"]

    novo_total = indicador["total_vendas"] + 1
    novo_nivel = _proximo_nivel(indicador["nivel"], novo_total)

    db.execute(
        """UPDATE indicadores
           SET total_vendas = ?, total_ganhos = total_ganhos + ?, nivel = ?,
               atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now')
           WHERE id = ?""",
        (novo_total, comissao, novo_nivel, indicador["id"]),
    )
    return comissao


@bp.get("")
def list_indicacoes():
    db = get_db()
    filters, params = [], []

    if status := request.args.get("status"):
        filters.append("i.status = ?")
        params.append(status)
    if indicador_id := request.args.get("indicador_id"):
        filters.append("i.indicador_id = ?")
        params.append(indicador_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"""SELECT i.*, ind.nome AS indicador_nome, ind.codigo_indicacao AS indicador_codigo
            FROM indicacoes i JOIN indicadores ind ON ind.id = i.indicador_id
            {where} ORDER BY i.criado_em DESC""",
        f"SELECT COUNT(*) FROM indicacoes i {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/resumo")
def resumo_por_indicador():
    db = get_db()
    rows = db.execute(
        """SELECT
             ind.id, ind.nome, ind.codigo_indicacao, ind.nivel, ind.total_ganhos,
             COUNT(i.id) AS total_indicacoes,
             SUM(CASE WHEN i.status IN ('em_atendimento','negociacao') THEN 1 ELSE 0 END) AS em_andamento,
             SUM(CASE WHEN i.status = 'fechado' THEN 1 ELSE 0 END) AS fechados,
             SUM(CASE WHEN i.status IN ('perdido','cancelado') THEN 1 ELSE 0 END) AS cancelados
           FROM indicadores ind
           LEFT JOIN indicacoes i ON i.indicador_id = ind.id
           GROUP BY ind.id
           ORDER BY ind.nome"""
    ).fetchall()
    return jsonify({"data": [_row_to_dict(r) for r in rows]})


@bp.get("/<int:indicacao_id>")
def get_indicacao(indicacao_id):
    db = get_db()
    return jsonify(_row_to_dict(_get_or_404(db, indicacao_id)))


@bp.patch("/<int:indicacao_id>")
def update_indicacao(indicacao_id):
    db = get_db()
    indicacao = _get_or_404(db, indicacao_id)
    body = request.get_json(force=True, silent=True) or {}

    if "status" in body and body["status"] not in STATUS_VALIDOS:
        raise ApiError("VALIDATION_ERROR", f"'status' deve ser um de {STATUS_VALIDOS}", 400)
    if "resultado" in body and body["resultado"] not in (*RESULTADOS_VALIDOS, None):
        raise ApiError("VALIDATION_ERROR", f"'resultado' deve ser um de {RESULTADOS_VALIDOS}", 400)

    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}
    fechando_agora = updates.get("status") == "fechado" and indicacao["status"] != "fechado"

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), indicacao_id]
        db.execute(
            f"UPDATE indicacoes SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )

    if fechando_agora:
        valor_sistema = updates.get("valor_sistema", indicacao["valor_sistema"])
        comissao = _fechar_indicacao(db, indicacao, valor_sistema)
        db.execute("UPDATE indicacoes SET comissao_gerada = ? WHERE id = ?", (comissao, indicacao_id))

    db.commit()
    log_activity(
        db, "update", "indicacoes", indicacao_id,
        f"Atendimento de {indicacao['nome_indicado']} encerrado por {g.user['nome']}"
        if fechando_agora else f"Indicação #{indicacao_id} atualizada por {g.user['nome']}",
    )
    row = db.execute("SELECT * FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.get("/<int:indicacao_id>/mensagens")
def list_mensagens(indicacao_id):
    db = get_db()
    _get_or_404(db, indicacao_id)
    rows = db.execute(
        "SELECT * FROM mensagens WHERE indicacao_id = ? ORDER BY criado_em, id", (indicacao_id,)
    ).fetchall()
    return jsonify({"data": [_row_to_dict(r) for r in rows]})


@bp.post("/<int:indicacao_id>/mensagens")
def enviar_mensagem(indicacao_id):
    db = get_db()
    _get_or_404(db, indicacao_id)
    body = request.get_json(force=True, silent=True) or {}
    texto = (body.get("texto") or "").strip()
    if not texto:
        raise ApiError("VALIDATION_ERROR", "Campo 'texto' é obrigatório", 400)

    cur = db.execute(
        "INSERT INTO mensagens (indicacao_id, autor_tipo, autor_usuario_id, texto) VALUES (?, 'operador', ?, ?)",
        (indicacao_id, g.user["id"], texto),
    )
    db.commit()
    row = db.execute("SELECT * FROM mensagens WHERE id = ?", (cur.lastrowid,)).fetchone()
    mensagem = _row_to_dict(row)
    broadcast_mensagem(indicacao_id, mensagem)
    return jsonify(mensagem), 201
