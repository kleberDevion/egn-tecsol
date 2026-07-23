"""Configuracao dos testes.

Os testes rodam contra um banco PostgreSQL separado (`tecsol_test`), criado
automaticamente se nao existir, e limpo entre cada teste. Nenhuma chamada real
a Solarz acontece: `app.solarz` e substituido por dublês (ver `solarz_falso`).

Rodar:  cd api && python -m pytest
"""

import os
import sys
from pathlib import Path

import psycopg
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Precisa vir antes de importar a app: create_app le essas variaveis.
DSN_ADMIN = os.environ.get("TEST_ADMIN_DSN", "postgresql://postgres:egn@127.0.0.1:5432/postgres")
DSN_TESTE = os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:egn@127.0.0.1:5432/tecsol_test")
os.environ["DATABASE_URL"] = DSN_TESTE
os.environ["SOLARZ_API_TOKEN"] = "token-de-teste"
os.environ["GOOGLE_ADS_WEBHOOK_KEY"] = "chave-de-teste"
os.environ.setdefault("SECRET_KEY", "segredo-de-teste")

from app import create_app  # noqa: E402
from app.db import get_db  # noqa: E402

TABELAS = [
    "comissoes", "geracoes_documentos", "mensagens", "indicacoes", "indicador_cliques",
    "leads_site", "indicadores", "suporte_avaliacoes", "suporte_mensagens", "suporte_threads",
    "activity_log", "usuario_grupos", "documentos", "geracao", "projetos", "usinas",
    "clientes", "concessionarias", "usuarios",
]


def _garante_banco():
    nome = DSN_TESTE.rsplit("/", 1)[-1]
    with psycopg.connect(DSN_ADMIN, autocommit=True) as conn:
        existe = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (nome,)).fetchone()
        if not existe:
            conn.execute(f'CREATE DATABASE "{nome}"')


@pytest.fixture(scope="session")
def app():
    _garante_banco()
    aplicacao = create_app()
    aplicacao.config.update(TESTING=True)
    return aplicacao


COMISSAO_PADRAO = ((1, 0.40), (2, 0.15), (3, 0.075))


@pytest.fixture(autouse=True)
def banco_limpo(app):
    """Zera as tabelas antes de cada teste, pra um teste nao depender do outro.

    `comissao_niveis` nao e truncada (ela vem do schema), mas precisa voltar ao
    padrao: um teste que altera o valor pelo painel de admin contaminaria o
    calculo de comissao dos testes seguintes."""
    with app.app_context():
        db = get_db()
        db.execute(f"TRUNCATE {', '.join(TABELAS)} RESTART IDENTITY CASCADE")
        for nivel, valor in COMISSAO_PADRAO:
            db.execute("UPDATE comissao_niveis SET valor_por_kwh = ? WHERE nivel = ?", (valor, nivel))
        db.commit()
    yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        yield get_db()


@pytest.fixture
def solarz_falso(monkeypatch):
    """Troca as chamadas à Solarz por dublês. Guarda o que foi "enviado" pra
    os testes conferirem funil/estagio sem depender da rede."""
    chamadas = {"negocios": [], "deal_id": 9000}

    def criar_negocio(**kwargs):
        chamadas["deal_id"] += 1
        chamadas["negocios"].append(kwargs)
        return chamadas["deal_id"]

    import app.routes.indicacoes_publicas as pub
    import app.routes.indicadores as ind
    import app.routes.leads_google_ads as ads
    import app.routes.leads_site as site

    for modulo in (pub, ind, site, ads):
        monkeypatch.setattr(modulo, "criar_negocio", criar_negocio)

    return chamadas


@pytest.fixture
def admin(client, db):
    """Cria um usuario admin e devolve o client ja logado."""
    from app.auth import hash_password

    db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, papel) VALUES (?, ?, ?, 'admin')",
        ("Admin Teste", "admin@teste.com", hash_password("senha12345")),
    )
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"email": "admin@teste.com", "senha": "senha12345"})
    assert resp.status_code == 200, resp.get_json()
    return client


@pytest.fixture
def indicador(client):
    """Cria um indicador e devolve (client logado, dados do indicador)."""
    resp = client.post(
        "/api/v1/indicadores/auth/signup",
        json={"nome": "Indicador Teste", "email": "ind@teste.com", "senha": "senha12345", "telefone": "27999990000"},
    )
    assert resp.status_code == 201, resp.get_json()
    return client, resp.get_json()
