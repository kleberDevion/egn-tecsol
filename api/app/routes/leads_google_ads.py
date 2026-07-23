import logging
import os

from flask import Blueprint, jsonify, request

from app.db import get_db
from app.errors import ApiError
from app.solarz import PIPELINE_PRE_VENDAS, STAGE_PRE_VENDAS_PROSPECT, SolarzApiError, criar_negocio

bp = Blueprint("leads_google_ads", __name__, url_prefix="/api/v1/publico/leads-google")

logger = logging.getLogger(__name__)

# Webhook dos formulários de lead do Google Ads. Não precisa de API, OAuth nem
# developer token: o Google faz POST aqui a cada lead. No painel do Ads
# (Ativos > Formulários de lead > Opções de entrega) informa-se esta URL e uma
# chave, que chega no corpo como "key" e é conferida abaixo.
#
# Formato do corpo (documentado pelo Google):
#   {"lead_id": "...", "form_id": 123, "campaign_id": 456, "gcl_id": "...",
#    "is_test": true, "key": "...",
#    "user_column_data": [{"column_id": "FULL_NAME", "string_value": "..."}]}

# column_id -> campo nosso
COLUNAS = {
    "FULL_NAME": "nome",
    "FIRST_NAME": "nome",
    "PHONE_NUMBER": "telefone",
    "EMAIL": "email",
    "CITY": "cidade",
    "POSTAL_CODE": "cep",
}


def _extrair(body):
    dados = {}
    for campo in body.get("user_column_data") or []:
        chave = COLUNAS.get((campo.get("column_id") or "").upper())
        if chave and not dados.get(chave):
            dados[chave] = campo.get("string_value")
    return dados


@bp.post("")
def receber_lead():
    chave_esperada = os.environ.get("GOOGLE_ADS_WEBHOOK_KEY")
    body = request.get_json(force=True, silent=True) or {}

    if not chave_esperada:
        logger.error("GOOGLE_ADS_WEBHOOK_KEY não configurada — recusando webhook.")
        raise ApiError("CONFIG_ERROR", "Webhook não configurado", 503)
    if body.get("key") != chave_esperada:
        raise ApiError("UNAUTHORIZED", "Chave inválida", 401)

    # O Google manda um lead de teste ao salvar o formulário: responder 200 é o
    # que valida a URL no painel dele, mas não queremos gravar isso como lead.
    if body.get("is_test"):
        return jsonify({"status": "ok", "teste": True})

    dados = _extrair(body)
    nome = (dados.get("nome") or "").strip()
    telefone = (dados.get("telefone") or "").strip()
    if not nome or not telefone:
        logger.warning("Lead do Ads sem nome/telefone: %s", body.get("lead_id"))
        raise ApiError("VALIDATION_ERROR", "Lead sem nome ou telefone", 400)

    db = get_db()
    cur = db.execute(
        """INSERT INTO leads_site (nome, telefone, email, cidade, origem, pagina)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nome, telefone, dados.get("email"), dados.get("cidade"),
         "google_ads", f"campanha:{body.get('campaign_id')}"),
    )
    db.commit()
    lead_id = cur.lastrowid

    try:
        deal_id = criar_negocio(
            nome_negocio=f"Google Ads - {nome}",
            pipeline_id=PIPELINE_PRE_VENDAS,
            pipeline_stage_id=STAGE_PRE_VENDAS_PROSPECT,
            pessoa_nome=nome,
            pessoa_telefone=telefone,
        )
        db.execute("UPDATE leads_site SET solarz_deal_id = ? WHERE id = ?", (deal_id, lead_id))
        db.commit()
    except SolarzApiError as e:
        logger.error("Falha ao criar negócio na Solarz para lead do Ads %s: %s", lead_id, e)

    return jsonify({"status": "ok", "id": lead_id})
