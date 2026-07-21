"""Execução manual/debug da sincronização com a Solarz:

    python sync_solarz.py

Em produção quem agenda é o Celery beat (app/tasks.py, a cada 15 min) — este
script existe pra rodar uma passada avulsa sem depender de broker/worker.
A lógica em si vive em app/sync_indicacoes.py.
"""

import logging

from app import create_app
from app.db import get_db
from app.sync_indicacoes import sincronizar

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        sincronizar(get_db())
