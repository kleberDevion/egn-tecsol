"""Núcleo da sincronização indicações <-> negócios da Solarz.

Usado por três entradas:
  - tarefa Dramatiq periódica (app/tasks.py) — o "cron" oficial;
  - POST /api/v1/indicadores/sync — botão "Atualizar" do app, sincroniza na
    hora só as indicações do indicador logado;
  - python sync_solarz.py — execução manual/debug.

O vínculo com o negócio é SEMPRE pelo telefone do indicado: o id de negócio da
Solarz muda quando ele troca de funil (confirmado pelos devs deles), então o
`solarz_deal_id` gravado serve só como referência do momento.

Comissão (regra do dono do app): paga por kWh de geração esperada do sistema,
lida da PROPOSTA da Solarz (custom field "Geração do Sistema (kWh/mês):" no
GET /v2/open-api/proposals, vinculada por personId). Multi-nível pela cadeia
de recrutamento (indicadores.recrutado_por_id):
  nível 1 = quem indicou o cliente; nível 2 = quem recrutou o nível 1;
  nível 3 = quem recrutou o nível 2. Valores R$/kWh na tabela comissao_niveis
(seed 0.40 / 0.15 / 0.075, editável pelo admin).

Se a indicação fecha mas a proposta ainda não tem a geração preenchida, a
comissão fica pendente (comissao_gerada NULL) e é recalculada nas próximas
passadas até o dado aparecer.
"""

import logging
import re

from app.solarz import (
    PIPELINE_PRE_VENDAS,
    PIPELINE_PRE_VENDAS_IA,
    PIPELINE_VENDAS,
    STAGE_VENDAS_CONTRATO_ASSINADO,
    SolarzApiError,
    buscar_pessoa_por_telefone,
    listar_negocios,
    listar_propostas,
)

logger = logging.getLogger(__name__)

STATUS_ABERTOS = ("recebido", "em_atendimento", "negociacao")

# O nome oficial do campo (definido pelo dono) é "Geração esperada" — ele tem
# prioridade. O genérico cobre o label que existe hoje nas propostas da conta
# ("Geração do Sistema (kWh/mês):") enquanto o campo oficial não é criado.
RE_LABEL_GERACAO_ESPERADA = re.compile(r"gera[çc][ãa]o\s*esperada", re.IGNORECASE)
RE_LABEL_GERACAO = re.compile(r"gera[çc][ãa]o", re.IGNORECASE)


def _so_digitos(telefone):
    return re.sub(r"\D", "", telefone or "")


def _proximo_nivel(nivel_atual, total_vendas):
    """Progressão de nível do indicador conforme vendas fechadas (mesmas
    faixas do app original). Morava em routes/indicacoes.py junto do cálculo
    antigo de comissão; veio pra cá quando aquele cálculo foi removido."""
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


def _para_float(valor):
    """Extrai o número de valores digitados livremente no CRM: "400",
    "400 kWh", "1.234,56", "6.82"..."""
    if valor is None:
        return None
    texto = str(valor)
    m = re.search(r"\d[\d.,]*", texto)
    if not m:
        return None
    numero = m.group()
    if "," in numero:
        numero = numero.replace(".", "").replace(",", ".")
    try:
        return float(numero)
    except ValueError:
        return None


def _mapear_status(status, pipeline_id, stage_id):
    if status == "LOST":
        return "perdido"
    if status in ("REJECTED", "DELETED"):
        return "cancelado"

    if pipeline_id in (PIPELINE_PRE_VENDAS_IA, PIPELINE_PRE_VENDAS):
        return "em_atendimento"
    if pipeline_id == PIPELINE_VENDAS:
        return "fechado" if stage_id == STAGE_VENDAS_CONTRATO_ASSINADO else "negociacao"
    # Qualquer pipeline pós-Vendas (Engenharia, Obras, Financeiro, Pós-*)
    # só existe depois do contrato assinado.
    return "fechado"


def _carregar_negocios_por_pessoa():
    """Uma passada só na listagem (itens têm personId/pipelineId flat) e
    indexa o negócio mais recente por personId."""
    por_pessoa = {}
    page = 0
    while True:
        data = listar_negocios(page=page, size=100)
        for deal in data.get("content", []):
            pid = deal.get("personId")
            if pid is None:
                continue
            atual = por_pessoa.get(pid)
            if atual is None or (deal.get("createdAt") or "") > (atual.get("createdAt") or ""):
                por_pessoa[pid] = deal
        if data.get("last", True):
            break
        page += 1
    return por_pessoa


def _extrair_geracao(campos):
    # "Geração esperada" (nome oficial) ganha de qualquer outro label com
    # "geração", se os dois existirem no mesmo formulário.
    for regex in (RE_LABEL_GERACAO_ESPERADA, RE_LABEL_GERACAO):
        for campo in campos or []:
            if regex.search(campo.get("label") or ""):
                kwh = _para_float(campo.get("value"))
                if kwh:
                    return kwh
    return None


def _carregar_geracao():
    """Indexa o kWh/mês de geração esperada da proposta mais recente que tiver
    o campo preenchido — por personId e, quando a proposta não está vinculada
    a uma pessoa, por dealId."""
    por_pessoa, por_deal, criacao = {}, {}, {}
    page = 0
    while True:
        data = listar_propostas(page=page, size=100)
        for prop in data.get("content", []):
            kwh = None
            for area in ("initialDataCustomFieldValues", "plantDataCustomFieldValues", "intermediateDataCustomFieldValues"):
                kwh = _extrair_geracao(prop.get(area))
                if kwh:
                    break
            if not kwh:
                continue
            quando = prop.get("creationDate") or ""
            for chave, indice in ((prop.get("personId"), por_pessoa), (prop.get("dealId"), por_deal)):
                if chave is not None and (chave not in indice or quando > criacao[(id(indice), chave)]):
                    indice[chave] = kwh
                    criacao[(id(indice), chave)] = quando
        if data.get("last", True):
            break
        page += 1
    return por_pessoa, por_deal


def _geracao_da_indicacao(pessoa_id, deal, geracao_pessoa, geracao_deal):
    """Fonte primária: proposta (por pessoa, depois por deal). Fallback: um
    custom field de geração no próprio negócio, caso a Tecsol crie um campo
    "Geração esperada" no formulário do deal em vez de emitir proposta."""
    kwh = geracao_pessoa.get(pessoa_id) or geracao_deal.get(deal["id"])
    if kwh:
        return kwh
    return _extrair_geracao(deal.get("dealCustomFieldValues"))


def _aplicar_comissao(db, indicacao_id, indicador_id, kwh):
    """Credita a comissão multi-nível de uma venda fechada. Idempotente: se já
    existe extrato pra essa indicação, não credita de novo. Retorna o valor do
    nível 1 (gravado em indicacoes.comissao_gerada)."""
    ja_tem = db.execute("SELECT 1 FROM comissoes WHERE indicacao_id = ?", (indicacao_id,)).fetchone()
    if ja_tem:
        return None

    valores = {r["nivel"]: r["valor_por_kwh"] for r in db.execute("SELECT * FROM comissao_niveis")}

    valor_n1 = None
    beneficiario_id = indicador_id
    for nivel in (1, 2, 3):
        if beneficiario_id is None or nivel not in valores:
            break
        indicador = db.execute("SELECT * FROM indicadores WHERE id = ?", (beneficiario_id,)).fetchone()
        if indicador is None:
            break

        valor = round(kwh * valores[nivel], 2)
        db.execute(
            "INSERT INTO comissoes (indicacao_id, indicador_id, nivel, kwh, valor_por_kwh, valor) VALUES (?,?,?,?,?,?)",
            (indicacao_id, beneficiario_id, nivel, kwh, valores[nivel], valor),
        )

        if nivel == 1:
            valor_n1 = valor
            novo_total = indicador["total_vendas"] + 1
            db.execute(
                """UPDATE indicadores SET total_vendas = ?, total_ganhos = total_ganhos + ?, nivel = ?,
                   atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?""",
                (novo_total, valor, _proximo_nivel(indicador["nivel"], novo_total), beneficiario_id),
            )
        else:
            db.execute(
                """UPDATE indicadores SET total_ganhos = total_ganhos + ?,
                   atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?""",
                (valor, beneficiario_id),
            )
        logger.info(
            "Comissão nível %s: R$ %.2f (%.1f kWh x %.3f) -> indicador %s (indicação %s)",
            nivel, valor, kwh, valores[nivel], beneficiario_id, indicacao_id,
        )
        beneficiario_id = indicador["recrutado_por_id"]

    return valor_n1


def sincronizar(db, indicador_id=None):
    """Sincroniza as indicações (todas, ou só de um indicador): status vindo
    do negócio na Solarz + comissão quando fecha. Também repesca indicações já
    fechadas cuja comissão ficou pendente por falta da geração na proposta.
    Retorna quantas foram atualizadas."""
    placeholders = ",".join("?" * len(STATUS_ABERTOS))
    query = (
        f"SELECT id, indicador_id, solarz_deal_id, telefone_indicado, status, comissao_gerada "
        f"FROM indicacoes WHERE (status IN ({placeholders}) "
        f"OR (status = 'fechado' AND comissao_gerada IS NULL))"
    )
    params = list(STATUS_ABERTOS)
    if indicador_id is not None:
        query += " AND indicador_id = ?"
        params.append(indicador_id)

    rows = db.execute(query, params).fetchall()
    if not rows:
        logger.info("Nada pra sincronizar.")
        return 0

    negocios_por_pessoa = _carregar_negocios_por_pessoa()
    geracao_pessoa, geracao_deal = _carregar_geracao()

    atualizados = 0
    for row in rows:
        digitos = _so_digitos(row["telefone_indicado"])
        if not digitos:
            continue

        pessoa = None
        try:
            # A Solarz guarda com DDI (5527...); tentamos como veio e com 55.
            for candidato in (digitos, f"55{digitos}"):
                pessoa = buscar_pessoa_por_telefone(candidato)
                if pessoa:
                    break
        except SolarzApiError as e:
            logger.error("Indicação %s: falha ao buscar pessoa: %s", row["id"], e)
            continue

        if pessoa is None:
            logger.info("Indicação %s: pessoa não encontrada na Solarz (tel %s).", row["id"], digitos)
            continue

        deal = negocios_por_pessoa.get(pessoa["id"])
        if deal is None:
            logger.info("Indicação %s: pessoa %s sem negócio na Solarz.", row["id"], pessoa["id"])
            continue

        novo_status = _mapear_status(deal.get("status"), deal.get("pipelineId"), deal.get("pipelineStageId"))

        updates, params = [], []
        if deal["id"] != row["solarz_deal_id"]:
            updates.append("solarz_deal_id = ?")
            params.append(deal["id"])
        if novo_status != row["status"]:
            updates.append("status = ?")
            params.append(novo_status)
            logger.info("Indicação %s: %s -> %s (deal %s)", row["id"], row["status"], novo_status, deal["id"])
        if novo_status == "fechado" and deal.get("value"):
            updates.append("valor_sistema = ?")
            params.append(deal["value"])

        if novo_status == "fechado" and row["comissao_gerada"] is None:
            kwh = _geracao_da_indicacao(pessoa["id"], deal, geracao_pessoa, geracao_deal)
            if kwh:
                comissao = _aplicar_comissao(db, row["id"], row["indicador_id"], kwh)
                if comissao is not None:
                    updates.append("comissao_gerada = ?")
                    params.append(comissao)
            else:
                logger.info(
                    "Indicação %s: fechada, mas proposta da pessoa %s ainda sem geração (kWh) — comissão pendente.",
                    row["id"], pessoa["id"],
                )

        if updates:
            params.append(row["id"])
            db.execute(
                f"UPDATE indicacoes SET {', '.join(updates)}, "
                f"atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
                params,
            )
            atualizados += 1

    db.commit()
    logger.info("Sincronização concluída: %s de %s indicações atualizadas.", atualizados, len(rows))
    return atualizados
