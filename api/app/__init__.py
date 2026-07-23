import os
from pathlib import Path

from flask import Flask, request


def _load_dotenv():
    """Carrega o .env pro os.environ (sem sobrescrever o que já existe).
    Feito na mão pra não depender do python-dotenv — o arquivo só tem
    CHAVE=valor por linha (ex: SOLARZ_API_TOKEN).

    Procura em api/.env e na raiz do repositório: em dev o arquivo fica junto
    da API, e na hospedagem (secret file da Render, por exemplo) ele pode cair
    na raiz do projeto. Variáveis já definidas no ambiente sempre vencem."""
    api_dir = Path(__file__).resolve().parent.parent
    for env_path in (api_dir / ".env", api_dir.parent / ".env"):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            # aspas em volta do valor são comuns em .env e não fazem parte dele
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

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
    geracao_documentos,
    indicadores,
    leads_google_ads,
    leads_site,
    mensagens_publicas,
    niveis,
    projetos,
    suporte,
    usinas,
    usuarios,
)
from app.socket import socketio


def _origens_permitidas():
    """Lista branca de origens (CORS_ORIGINS, separada por vírgula). Vazia =
    reflete qualquer origem, que é o comportamento cômodo de desenvolvimento.
    Em produção SEMPRE definir, porque a API responde com credenciais."""
    valor = os.environ.get("CORS_ORIGINS", "").strip()
    return [o.strip().rstrip("/") for o in valor.split(",") if o.strip()]


def _apply_cors(response):
    origin = request.headers.get("Origin")
    permitidas = _origens_permitidas()
    if origin and (not permitidas or origin.rstrip("/") in permitidas):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def create_app(test_config=None):
    _load_dotenv()
    app = Flask(__name__)
    # Em produção a API fica num host diferente dos frontends (ex:
    # tecsol-api.onrender.com x tecsol-parceiros.onrender.com). Pro navegador
    # isso é cross-site, e o cookie de sessão só viaja com SameSite=None +
    # Secure (que exige HTTPS — por isso não vale em dev, no http local).
    cross_site = os.environ.get("COOKIE_CROSS_SITE", "").lower() in ("1", "true", "yes")
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-tecsol-secret-change-me"),
        AVATAR_DIR=str(Path(app.root_path).parent / "instance" / "avatars"),
        DOCUMENTOS_DIR=str(Path(app.root_path).parent / "instance" / "documentos"),
        MODELOS_DIR=os.environ.get("MODELOS_DIR", str(Path(app.root_path).parent / "templates_documentos")),
        DOCUMENTOS_GERADOS_DIR=os.environ.get(
            "DOCUMENTOS_GERADOS_DIR", str(Path(app.root_path).parent / "instance" / "gerados")
        ),
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="None" if cross_site else "Lax",
        SESSION_COOKIE_SECURE=cross_site,
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
    app.register_blueprint(leads_site.bp)
    app.register_blueprint(leads_google_ads.bp)
    app.register_blueprint(geracao_documentos.bp)
    app.register_blueprint(mensagens_publicas.bp)
    app.register_blueprint(niveis.bp)
    app.register_blueprint(suporte.bp)
    app.register_blueprint(grupos.bp)

    socketio.init_app(app)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app
