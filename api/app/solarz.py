"""Cliente para a API do CRM Solarz (https://api.crm.solarz.com.br), usada
para registrar os leads do app de indicações como negócios reais no CRM.

Autenticação: "Personal External API Key" da Solarz, enviada no header
`Authorization` (sem prefixo "Bearer"). Configurada via env var
SOLARZ_API_TOKEN — nunca hardcoded, nunca exposta ao frontend.
"""

import os
import time

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


def _request(method, path, _tentativas=4, **kwargs):
    for tentativa in range(_tentativas):
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

        # Rate limit: respeita Retry-After se vier, senão backoff exponencial.
        if res.status_code == 429 and tentativa < _tentativas - 1:
            espera = float(res.headers.get("Retry-After") or 2 ** (tentativa + 1))
            time.sleep(min(espera, 30))
            continue

        if not res.ok:
            raise SolarzApiError(f"Solarz respondeu {res.status_code}: {res.text[:500]}", res.status_code)
        return res.json() if res.content else None


def criar_negocio(*, nome_negocio, pipeline_id, pipeline_stage_id, pessoa_nome, pessoa_telefone):
    """Cria pessoa + negócio na Solarz numa única chamada. Retorna o dealId.

    Atenção: o id retornado NÃO é estável — os devs da Solarz confirmaram que o
    id de negócio muda quando ele troca de funil. O vínculo confiável com a
    indicação local é o telefone da pessoa (ver sync_solarz.py)."""
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


def buscar_pessoa_por_telefone(telefone):
    """Busca a pessoa no CRM pelo telefone. Retorna a primeira ou None."""
    data = _request("GET", f"/v2/open-api/client/persons?phone={telefone}&page=0&size=1")
    content = data.get("content") or []
    return content[0] if content else None


def listar_negocios(page=0, size=100, pipeline_id=None):
    """Listagem paginada de negócios (itens vêm com personId/pipelineId flat,
    sem os objetos aninhados do GET /deal/{id})."""
    qs = f"page={page}&size={size}"
    if pipeline_id:
        qs += f"&pipelineId={pipeline_id}"
    return _request("GET", f"/v2/open-api/deal?{qs}")


def listar_propostas(page=0, size=100):
    """Listagem paginada de propostas. É aqui (e não no deal) que vive a
    geração esperada do sistema: custom field "Geração do Sistema (kWh/mês):"
    em initialDataCustomFieldValues, vinculada à pessoa por personId."""
    return _request("GET", f"/v2/open-api/proposals?page={page}&size={size}")
