"""Dramatiq: fila e agendamento da sincronização com a Solarz.

Broker: Redis, via env REDIS_URL (default redis://127.0.0.1:6379/0). A Render
oferece Redis gerenciado ("Key Value"), mas não RabbitMQ — por isso o broker
é Redis, não AMQP.

Como rodar:
    dramatiq app.tasks --processes 1 --threads 2    # worker
    periodiq app.tasks                              # agendador (cron)

O periodiq dispara a sync a cada 15 minutos (crontab abaixo). Além disso,
run.py enfileira uma execução imediata na subida do servidor — e, se o broker
estiver fora do ar, cai num fallback inline pra sync inicial não deixar de
acontecer.
"""

import os

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from periodiq import PeriodiqMiddleware, cron

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

broker = RedisBroker(url=REDIS_URL)
broker.add_middleware(PeriodiqMiddleware(skip_delay=30))
dramatiq.set_broker(broker)


@dramatiq.actor(periodic=cron("*/15 * * * *"), max_retries=3)
def sync_solarz():
    # Imports adiados: o worker importa este módulo antes de existir um app
    # Flask; cada execução cria o próprio contexto.
    from app import create_app
    from app.db import get_db
    from app.sync_indicacoes import sincronizar

    app = create_app()
    with app.app_context():
        sincronizar(get_db())


@dramatiq.actor(max_retries=1, time_limit=600_000)
def gerar_documentos(geracao_id):
    """Gera os .docx de um negócio. Roda fora do request porque envolve várias
    chamadas à Solarz + escrita em disco."""
    from app import create_app
    from app.db import get_db
    from app.geracao_documentos import executar

    app = create_app()
    with app.app_context():
        executar(get_db(), geracao_id, app.config["MODELOS_DIR"])
