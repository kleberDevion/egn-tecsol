"""Acesso ao banco (PostgreSQL).

Migrado do SQLite em 2026-07-21. Pra não reescrever as ~176 queries espalhadas
pelas rotas, este módulo expõe a MESMA interface que o `sqlite3` oferecia:

    db.execute("SELECT * FROM x WHERE id = ?", (1,)).fetchone()["nome"]
    cur = db.execute("INSERT INTO x (...) VALUES (?, ?)", (...)); cur.lastrowid

A tradução SQLite -> PostgreSQL acontece em `_traduzir()`:
  - `?`                       -> `%s` (respeitando aspas simples)
  - `strftime(...,'now')`     -> `to_char(now() at time zone 'utc', ...)`
  - `lower(hex(randomblob))`  -> `md5(random()::text || clock_timestamp()::text)`
  - INSERT sem RETURNING      -> ganha `RETURNING id` (pra alimentar lastrowid)

As linhas voltam como `Row`, que aceita índice (`row[0]`) e nome (`row["nome"]`)
e converte com `dict(row)` — igual ao `sqlite3.Row`.
"""

import os
import re
from pathlib import Path

import psycopg
from flask import current_app, g

SQLITE_AGORA = "strftime('%Y-%m-%dT%H:%M:%SZ','now')"
PG_AGORA = "to_char(now() AT TIME ZONE 'utc', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')"
SQLITE_TOKEN = "lower(hex(randomblob(16)))"
PG_TOKEN = "md5(random()::text || clock_timestamp()::text)"

# Tabelas sem coluna `id` — nelas o INSERT não pode receber `RETURNING id`.
TABELAS_SEM_ID = {"usuario_grupos", "grupos", "configuracoes", "niveis_config", "comissao_niveis"}

_RE_INSERT_TABELA = re.compile(r"^\s*INSERT\s+INTO\s+([a-z_]+)", re.IGNORECASE)
# No SQLite o LIKE é case-insensitive (ASCII); no PostgreSQL não. As buscas por
# nome/código dos contratos prometem case-insensitive, então viram ILIKE.
_RE_LIKE = re.compile(r"(?<![a-zA-Z])LIKE\b", re.IGNORECASE)


def _troca_placeholders(sql):
    """`?` -> `%s`, sem tocar no que estiver dentro de aspas simples."""
    saida, dentro_de_aspas = [], False
    for ch in sql:
        if ch == "'":
            dentro_de_aspas = not dentro_de_aspas
        if ch == "?" and not dentro_de_aspas:
            saida.append("%s")
        else:
            saida.append(ch)
    return "".join(saida)


def _traduzir(sql):
    sql = sql.replace(SQLITE_AGORA, PG_AGORA).replace(SQLITE_TOKEN, PG_TOKEN)
    sql = _RE_LIKE.sub("ILIKE", sql)
    sql = _troca_placeholders(sql)

    m = _RE_INSERT_TABELA.match(sql)
    if m and m.group(1).lower() not in TABELAS_SEM_ID and "returning" not in sql.lower():
        sql = sql.rstrip().rstrip(";") + " RETURNING id"
    return sql


class Row:
    """Linha acessível por índice e por nome, conversível com dict()."""

    __slots__ = ("_valores", "_colunas")

    def __init__(self, valores, colunas):
        self._valores = valores
        self._colunas = colunas

    def __getitem__(self, chave):
        if isinstance(chave, int):
            return self._valores[chave]
        return self._valores[self._colunas.index(chave)]

    def keys(self):
        return list(self._colunas)

    def __iter__(self):
        return iter(self._valores)

    def __len__(self):
        return len(self._valores)

    def __contains__(self, chave):
        return chave in self._colunas

    def __repr__(self):
        return f"Row({dict(zip(self._colunas, self._valores))})"


class Cursor:
    def __init__(self, cur, lastrowid=None):
        self._cur = cur
        self.lastrowid = lastrowid

    @property
    def _colunas(self):
        return [d.name for d in (self._cur.description or [])]

    def fetchone(self):
        linha = self._cur.fetchone()
        return Row(linha, self._colunas) if linha is not None else None

    def fetchall(self):
        colunas = self._colunas
        return [Row(linha, colunas) for linha in self._cur.fetchall()]

    def __iter__(self):
        colunas = self._colunas
        for linha in self._cur:
            yield Row(linha, colunas)

    @property
    def rowcount(self):
        return self._cur.rowcount


class Connection:
    """Fachada com a mesma cara do sqlite3.Connection usada pelas rotas."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        sql_pg = _traduzir(sql)
        cur = self._conn.cursor()
        cur.execute(sql_pg, tuple(params) if params else None)

        lastrowid = None
        if sql_pg.rstrip().lower().endswith("returning id"):
            linha = cur.fetchone()
            lastrowid = linha[0] if linha else None
        return Cursor(cur, lastrowid)

    def executemany(self, sql, seq_params):
        # Sem RETURNING aqui: executemany é usado só para inserções em lote
        # (ex: grupos de um usuário), onde ninguém precisa do lastrowid.
        sql_pg = _traduzir(sql)
        if sql_pg.rstrip().lower().endswith("returning id"):
            sql_pg = sql_pg.rstrip()[: -len("RETURNING id")].rstrip()
        cur = self._conn.cursor()
        cur.executemany(sql_pg, [tuple(p) for p in seq_params])
        return Cursor(cur)

    def executescript(self, sql):
        with self._conn.cursor() as cur:
            cur.execute(sql)
        self._conn.commit()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def _dsn():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL não configurado (ver api/.env)")
    return dsn


def get_db():
    if "db" not in g:
        g.db = Connection(psycopg.connect(_dsn()))
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _ensure_columns(conn):
    """Colunas adicionadas depois que o schema já rodava em produção. No
    PostgreSQL o `IF NOT EXISTS` resolve sem consultar o catálogo antes."""
    conn.executescript(
        """
        ALTER TABLE usuarios   ADD COLUMN IF NOT EXISTS foto_path TEXT;
        ALTER TABLE usuarios   ADD COLUMN IF NOT EXISTS foto_bytes BYTEA;
        ALTER TABLE usuarios   ADD COLUMN IF NOT EXISTS foto_tipo TEXT;
        ALTER TABLE projetos   ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ativo';
        ALTER TABLE indicacoes ADD COLUMN IF NOT EXISTS chat_token TEXT;
        ALTER TABLE indicacoes ADD COLUMN IF NOT EXISTS solarz_deal_id INTEGER;
        ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS recrutado_por_id INTEGER REFERENCES indicadores(id);
        ALTER TABLE geracoes_documentos ADD COLUMN IF NOT EXISTS contexto TEXT;
        UPDATE indicacoes SET chat_token = md5(random()::text || clock_timestamp()::text)
         WHERE chat_token IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_indicacoes_chat_token ON indicacoes(chat_token);
        """
    )


def init_db(app):
    schema_path = Path(app.root_path).parent / "schema.sql"
    conn = Connection(psycopg.connect(_dsn()))
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        _ensure_columns(conn)
        conn.commit()
    finally:
        conn.close()
