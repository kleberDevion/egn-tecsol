import logging
import os
import threading

from app import create_app
from app.socket import socketio

logger = logging.getLogger(__name__)

app = create_app()


def _sync_inicial():
    """Dispara a sincronização com a Solarz imediatamente na subida do
    servidor (o recorrente de 15 em 15 min é do periodiq, app/tasks.py).
    Se o broker Redis não estiver acessível (ex: dev local sem Redis), roda
    inline numa thread pra sync inicial acontecer mesmo assim."""
    try:
        from app.tasks import sync_solarz

        sync_solarz.send()
        logger.info("Sync inicial enfileirada no Dramatiq.")
    except Exception as e:
        logger.warning("Broker Redis indisponível (%s) — rodando sync inicial inline.", e)

        def _inline():
            from app.db import get_db
            from app.sync_indicacoes import sincronizar

            try:
                with app.app_context():
                    sincronizar(get_db())
            except Exception:
                logger.exception("Sync inicial inline falhou")

        threading.Thread(target=_inline, daemon=True).start()


if __name__ == "__main__":
    # Com o reloader do modo debug (debug=True abaixo) o processo sobe duas
    # vezes; só a instância "filha" (WERKZEUG_RUN_MAIN=true) serve requisições
    # — e só ela dispara a sync inicial, senão rodaria em dobro.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        _sync_inicial()
    socketio.run(app, port=5000, debug=True)
