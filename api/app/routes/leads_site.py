import logging

from flask import Blueprint, jsonify, request

from app.db import get_db
from app.errors import ApiError
from app.solarz import PIPELINE_PRE_VENDAS, STAGE_PRE_VENDAS_PROSPECT, SolarzApiError, criar_negocio

bp = Blueprint("leads_site", __name__, url_prefix="/api/v1/publico/leads-site")

logger = logging.getLogger(__name__)

# Sem login: quem preenche é visitante do site institucional. Diferente das
# indicações, esse lead não pertence a nenhum indicador e não gera comissão —
# por isso vai pra tabela própria (leads_site) e cai no funil
# "Comercial - Pré-vendas" da Solarz (definido pelo dono do app).

CAMPOS_OPCIONAIS = ("email", "cidade", "tipo_solucao", "valor_conta", "mensagem", "origem", "pagina")


@bp.post("")
def criar_lead_site():
    body = request.get_json(force=True, silent=True) or {}
    nome = (body.get("nome") or "").strip()
    telefone = (body.get("telefone") or "").strip()
    if not nome:
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)
    if not telefone:
        raise ApiError("VALIDATION_ERROR", "Campo 'telefone' é obrigatório", 400)

    valores = [nome, telefone, *[(body.get(c) or None) for c in CAMPOS_OPCIONAIS]]
    colunas = ", ".join(("nome", "telefone", *CAMPOS_OPCIONAIS))
    placeholders = ", ".join("?" * len(valores))

    db = get_db()
    cur = db.execute(f"INSERT INTO leads_site ({colunas}) VALUES ({placeholders})", valores)
    db.commit()
    lead_id = cur.lastrowid

    # Falha na Solarz não derruba o cadastro: o lead já foi recebido e o
    # solarz_deal_id fica NULL até um retry manual.
    try:
        deal_id = criar_negocio(
            nome_negocio=f"Site - {nome}",
            pipeline_id=PIPELINE_PRE_VENDAS,
            pipeline_stage_id=STAGE_PRE_VENDAS_PROSPECT,
            pessoa_nome=nome,
            pessoa_telefone=telefone,
        )
        db.execute("UPDATE leads_site SET solarz_deal_id = ? WHERE id = ?", (deal_id, lead_id))
        db.commit()
    except SolarzApiError as e:
        logger.error("Falha ao criar negócio na Solarz para lead do site %s: %s", lead_id, e)

    return jsonify({"id": lead_id}), 201
