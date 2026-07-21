import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _ensure_columns(conn):
    cols = {row[1] for row in conn.execute("PRAGMA table_info(usuarios)")}
    if "foto_path" not in cols:
        conn.execute("ALTER TABLE usuarios ADD COLUMN foto_path TEXT")

    indicadores_cols = {row[1] for row in conn.execute("PRAGMA table_info(indicadores)")}
    if "recrutado_por_id" not in indicadores_cols:
        conn.execute("ALTER TABLE indicadores ADD COLUMN recrutado_por_id INTEGER REFERENCES indicadores(id)")

    indicacoes_cols = {row[1] for row in conn.execute("PRAGMA table_info(indicacoes)")}
    if "chat_token" not in indicacoes_cols:
        conn.execute("ALTER TABLE indicacoes ADD COLUMN chat_token TEXT")
        conn.execute("UPDATE indicacoes SET chat_token = lower(hex(randomblob(16))) WHERE chat_token IS NULL")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_indicacoes_chat_token ON indicacoes(chat_token)")
    if "solarz_deal_id" not in indicacoes_cols:
        conn.execute("ALTER TABLE indicacoes ADD COLUMN solarz_deal_id INTEGER")

    projetos_cols = {row[1] for row in conn.execute("PRAGMA table_info(projetos)")}
    if "status" not in projetos_cols:
        conn.execute("ALTER TABLE projetos ADD COLUMN status TEXT NOT NULL DEFAULT 'ativo'")


def _migrate_legacy_tables(conn):
    """Tabelas cujo formato mudou antes de terem dado real (mesma sessão de
    trabalho) — dropa a versão antiga pra ser recriada pelo schema.sql logo em
    seguida, em vez de tentar migrar linha a linha algo que nunca foi usado de
    verdade."""
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "suporte_mensagens" in tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(suporte_mensagens)")}
        if "thread_id" not in cols:
            conn.execute("DROP TABLE suporte_mensagens")


def init_db(app):
    schema_path = Path(app.root_path).parent / "schema.sql"
    conn = sqlite3.connect(app.config["DATABASE"])
    try:
        _migrate_legacy_tables(conn)
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        _ensure_columns(conn)
        conn.commit()
    finally:
        conn.close()
