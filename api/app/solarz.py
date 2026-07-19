"""Cliente para a API do CRM Solarz (https://api.crm.solarz.com.br), usada
para registrar os leads do app de indicações como negócios reais no CRM.

Autenticação: "Personal External API Key" da Solarz, enviada no header
`Authorization` (sem prefixo "Bearer"). Configurada via env var
SOLARZ_API_TOKEN — nunca hardcoded, nunca exposta ao frontend.
"""

import os

import requests

SOLARZ_API_BASE = os.environ.get("SOLARZ_API_BASE", "https://api.crm.solarz.com.br/api")

# Funis (pipelines) e estágios do CRM Solarz, conforme definido pela dona do
# app em reunião (2026-07-18) e confirmado via GET /v2/open-api/pipeline:
#   - lead pelo link público (form do indicado) entra no funil da IA;
#   - lead cadastrado direto no app pelo indicador entra no funil "normal".
PIPELINE_PRE_VENDAS_IA = 11248
STAGE_PRE_VENDAS_IA_TRIAGEM = 63513

PIPELINE_PRE_VENDAS = 7602
STAGE_PRE_VENDAS_PROSPECT = 42920

# "Comercial - Vendas": passar do estágio "Contrato Assinado" é o que a dona do
# app definiu como o negócio estar fechado.
PIPELINE_VENDAS = 7603
STAGE_VENDAS_CONTRATO_ASSINADO = 42933

# "Engenharia": vem depois de Vendas — usado hoje só pra reconhecer que o
# negócio já foi fechado (todo pipeline pós-Vendas conta como fechado).
PIPELINE_ENGENHARIA = 8305
STAGE_ENGENHARIA_ENTREGA_OFICIAL = 62420

# Dono padrão dos leads criados via integração (Kleber Santana, id confirmado
# via GET /v2/open-api/users). Pode virar configurável por env var no futuro
# se a regra de negócio mudar.
RESPONSIBLE_SELLER_ID = 9981


class SolarzApiError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def _token():
    token = os.environ.get("SOLARZ_API_TOKEN")
    if not token:
        raise SolarzApiError("SOLARZ_API_TOKEN não configurado")
    return token


def _request(method, path, **kwargs):
    try:
        res = requests.request(
            method,
            f"{SOLARZ_API_BASE}{path}",
            headers={"Authorization": _token(), "Content-Type": "application/json"},
            timeout=10,
            **kwargs,
        )
    except requests.RequestException as e:
        raise SolarzApiError(f"Falha de rede ao chamar a Solarz: {e}") from e

    if not res.ok:
        raise SolarzApiError(f"Solarz respondeu {res.status_code}: {res.text[:500]}", res.status_code)
    return res.json() if res.content else None


def criar_negocio(*, nome_negocio, pipeline_id, pipeline_stage_id, pessoa_nome, pessoa_telefone):
    """Cria pessoa + negócio na Solarz numa única chamada. Retorna o dealId."""
    body = {
        "deal": {
            "name": nome_negocio,
            "pipelineId": pipeline_id,
            "pipelineStageId": pipeline_stage_id,
            "ownerId": RESPONSIBLE_SELLER_ID,
        },
        "person": {
            "name": pessoa_nome,
            "phone": pessoa_telefone,
            "responsibleSellerId": RESPONSIBLE_SELLER_ID,
        },
    }
    data = _request("POST", "/v2/open-api/deal/with-person-org-activities", json=body)
    return data["id"]


def buscar_negocios(deal_ids):
    """Busca o status/pipeline/estágio atual de vários negócios de uma vez."""
    if not deal_ids:
        return []
    ids_qs = "&".join(f"ids={i}" for i in deal_ids)
    data = _request("GET", f"/v2/open-api/deal/find-all?{ids_qs}&page=0&size={len(deal_ids)}")
    return data["content"]
