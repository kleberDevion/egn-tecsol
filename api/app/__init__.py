import os
from pathlib import Path

from flask import Flask, request

from app.db import close_db, init_db
from app.errors import register_error_handlers
from app.routes import (
    admin,
    auth,
    clientes,
    concessionarias,
    dashboard,
    documentos,
    geracao,
    grupos,
    indicacoes,
    indicacoes_publicas,
    indicadores,
    mensagens_publicas,
    niveis,
    projetos,
    suporte,
    usinas,
    usuarios,
)
from app.socket import socketio


def _apply_cors(response):
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(Path(app.root_path).parent / "tecsol.db"),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-tecsol-secret-change-me"),
        AVATAR_DIR=str(Path(app.root_path).parent / "instance" / "avatars"),
        DOCUMENTOS_DIR=str(Path(app.root_path).parent / "instance" / "documentos"),
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    init_db(app)
    app.teardown_appcontext(close_db)
    register_error_handlers(app)

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            return _apply_cors(app.make_default_options_response())

    app.after_request(_apply_cors)

    app.register_blueprint(auth.bp)
    app.register_blueprint(usuarios.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(clientes.bp)
    app.register_blueprint(projetos.bp)
    app.register_blueprint(documentos.bp)
    app.register_blueprint(usinas.bp)
    app.register_blueprint(geracao.bp)
    app.register_blueprint(concessionarias.bp)
    app.register_blueprint(indicadores.bp)
    app.register_blueprint(indicacoes.bp)
    app.register_blueprint(indicacoes_publicas.bp)
    app.register_blueprint(mensagens_publicas.bp)
    app.register_blueprint(niveis.bp)
    app.register_blueprint(suporte.bp)
    app.register_blueprint(grupos.bp)

    socketio.init_app(app)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app
