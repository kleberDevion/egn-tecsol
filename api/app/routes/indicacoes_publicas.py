import logging

from flask import Blueprint, jsonify, request

from app.db import get_db
from app.errors import ApiError
from app.solarz import PIPELINE_PRE_VENDAS_IA, STAGE_PRE_VENDAS_IA_TRIAGEM, SolarzApiError, criar_negocio

bp = Blueprint("indicacoes_publicas", __name__, url_prefix="/api/v1/publico/indicadores")

logger = logging.getLogger(__name__)

# Sem login: quem acessa o link de indicação (/i/{codigo}) é o cliente
# indicado, que não tem conta em nenhum dos dois apps.


def _get_indicador_or_404(db, codigo):
    row = db.execute("SELECT * FROM indicadores WHERE codigo_indicacao = ? AND ativo = 1", (codigo,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", "Link de indicação não encontrado", 404)
    return row


@bp.get("/<codigo>")
def acessar_link(codigo):
    """Página pública do link (`GET /i/{codigo}` no front). Cada acesso conta
    como um clique nas estatísticas do indicador."""
    db = get_db()
    indicador = _get_indicador_or_404(db, codigo)
    db.execute("INSERT INTO indicador_cliques (indicador_id) VALUES (?)", (indicador["id"],))
    db.commit()
    return jsonify({"indicador_nome": indicador["nome"]})


@bp.post("/<codigo>/indicacoes")
def criar_indicacao_publica(codigo):
    db = get_db()
    indicador = _get_indicador_or_404(db, codigo)

    body = request.get_json(force=True, silent=True) or {}
    nome_indicado = body.get("nome_indicado")
    telefone_indicado = body.get("telefone_indicado")
    if not nome_indicado:
        raise ApiError("VALIDATION_ERROR", "Campo 'nome_indicado' é obrigatório", 400)
    if not telefone_indicado:
        raise ApiError("VALIDATION_ERROR", "Campo 'telefone_indicado' é obrigatório", 400)

    nivel_interesse = body.get("nivel_interesse", "nao_sei")
    if nivel_interesse not in ("sim", "talvez", "nao_sei"):
        raise ApiError("VALIDATION_ERROR", "nivel_interesse inválido", 400)

    cur = db.execute(
        """INSERT INTO indicacoes
           (indicador_id, nome_indicado, telefone_indicado, cidade, conta_energia_estimada, nivel_interesse, observacoes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            indicador["id"],
            nome_indicado,
            telefone_indicado,
            body.get("cidade"),
            body.get("conta_energia_estimada"),
            nivel_interesse,
            body.get("observacoes"),
        ),
    )
    db.commit()
    indicacao_id = cur.lastrowid

    # A Solarz é o CRM real onde a Tecsol trabalha o lead — se essa chamada
    # falhar (rede, token, etc.), não derruba o cadastro local: o lead já foi
    # recebido, e o solarz_deal_id fica NULL até um retry manual.
    try:
        deal_id = criar_negocio(
            nome_negocio=f"Indicação (link) - {nome_indicado}",
            pipeline_id=PIPELINE_PRE_VENDAS_IA,
            pipeline_stage_id=STAGE_PRE_VENDAS_IA_TRIAGEM,
            pessoa_nome=nome_indicado,
            pessoa_telefone=telefone_indicado,
        )
        db.execute("UPDATE indicacoes SET solarz_deal_id = ? WHERE id = ?", (deal_id, indicacao_id))
        db.commit()
    except SolarzApiError as e:
        logger.error("Falha ao criar negócio na Solarz para indicacao %s: %s", indicacao_id, e)

    row = db.execute("SELECT * FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone()
    return jsonify(dict(row)), 201
