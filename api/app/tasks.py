"""Dramatiq: fila e agendamento da sincronização com a Solarz.

Broker: RabbitMQ, via env RABBITMQ_URL (default amqp://guest:guest@127.0.0.1:5672).

Como rodar:
    dramatiq app.tasks --processes 1 --threads 1     # worker
    periodiq app.tasks                               # agendador (cron)

O periodiq dispara a sync a cada 15 minutos (crontab abaixo). Além disso,
run.py enfileira uma execução imediata na subida do servidor — e, se o broker
estiver fora do ar (ex: dev local sem RabbitMQ), cai num fallback inline pra
sync inicial não deixar de acontecer.
"""

import os

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from periodiq import PeriodiqMiddleware, cron

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672")

broker = RabbitmqBroker(url=RABBITMQ_URL)
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
