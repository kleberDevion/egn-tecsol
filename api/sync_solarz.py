"""Sincroniza o status das indicações com os negócios correspondentes na
Solarz. Rodar periodicamente (cron / Agendador de Tarefas):

    python sync_solarz.py

Só atualiza a coluna `status` — NÃO calcula comissão nem mexe em
total_vendas/nivel do indicador. Isso é proposital: o cálculo de comissão
(nível 1/2/3 por kWh de geração) ainda depende de descobrir onde a Solarz
guarda a geração estimada da proposta (pendente, ver conversa com os devs da
Solarz). Uma vez definido, plugar o cálculo aqui, no bloco `fechando_agora`.
"""

import logging

from app import create_app
from app.db import get_db
from app.solarz import (
    PIPELINE_ENGENHARIA,
    PIPELINE_PRE_VENDAS,
    PIPELINE_PRE_VENDAS_IA,
    PIPELINE_VENDAS,
    STAGE_VENDAS_CONTRATO_ASSINADO,
    SolarzApiError,
    buscar_negocios,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STATUS_ABERTOS = ("recebido", "em_atendimento", "negociacao")
LOTE = 50


def _mapear_status(deal):
    if deal["status"] == "LOST":
        return "perdido"
    if deal["status"] in ("REJECTED", "DELETED"):
        return "cancelado"

    pipeline_id = deal["pipeline"]["id"] if deal.get("pipeline") else None
    stage_id = deal["pipelineStage"]["id"] if deal.get("pipelineStage") else None

    if pipeline_id in (PIPELINE_PRE_VENDAS_IA, PIPELINE_PRE_VENDAS):
        return "em_atendimento"
    if pipeline_id == PIPELINE_VENDAS:
        return "fechado" if stage_id == STAGE_VENDAS_CONTRATO_ASSINADO else "negociacao"
    # Qualquer pipeline pós-Vendas (Engenharia, Obras, Financeiro, Pós-*)
    # só existe depois do contrato assinado.
    return "fechado"


def sync():
    app = create_app()
    with app.app_context():
        db = get_db()
        placeholders = ",".join("?" * len(STATUS_ABERTOS))
        rows = db.execute(
            f"SELECT id, solarz_deal_id, status FROM indicacoes "
            f"WHERE solarz_deal_id IS NOT NULL AND status IN ({placeholders})",
            STATUS_ABERTOS,
        ).fetchall()
        if not rows:
            logger.info("Nada pra sincronizar.")
            return

        por_deal_id = {r["solarz_deal_id"]: r for r in rows}
        deal_ids = list(por_deal_id.keys())
        atualizados = 0

        for i in range(0, len(deal_ids), LOTE):
            lote_ids = deal_ids[i : i + LOTE]
            try:
                deals = buscar_negocios(lote_ids)
            except SolarzApiError as e:
                logger.error("Falha ao buscar negócios %s na Solarz: %s", lote_ids, e)
                continue

            for deal in deals:
                indicacao = por_deal_id.get(deal["id"])
                if indicacao is None:
                    continue
                novo_status = _mapear_status(deal)
                if novo_status != indicacao["status"]:
                    db.execute(
                        "UPDATE indicacoes SET status = ?, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
                        (novo_status, indicacao["id"]),
                    )
                    atualizados += 1
                    logger.info(
                        "Indicação %s: %s -> %s (deal %s)",
                        indicacao["id"], indicacao["status"], novo_status, deal["id"],
                    )

        db.commit()
        logger.info("Sincronização concluída: %s indicações atualizadas de %s verificadas.", atualizados, len(rows))


if __name__ == "__main__":
    sync()
