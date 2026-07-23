"""Camada de compatibilidade SQLite -> PostgreSQL (app/db.py).

Ela existe pra manter as ~176 queries escritas em dialeto SQLite funcionando no
Postgres. Cada regra de traducao tem um teste aqui, porque um erro nessa camada
quebra o sistema inteiro de um jeito dificil de rastrear.
"""

from app.db import Row, _traduzir


class TestTraducao:
    def test_placeholder_vira_porcento_s(self):
        assert _traduzir("SELECT * FROM x WHERE id = ?") == "SELECT * FROM x WHERE id = %s"

    def test_nao_troca_interrogacao_dentro_de_aspas(self):
        sql = _traduzir("SELECT * FROM x WHERE nome = 'e ai?' AND id = ?")
        assert sql == "SELECT * FROM x WHERE nome = 'e ai?' AND id = %s"

    def test_strftime_vira_to_char(self):
        sql = _traduzir("UPDATE x SET em = strftime('%Y-%m-%dT%H:%M:%SZ','now')")
        assert "strftime" not in sql
        assert "to_char(now() AT TIME ZONE 'utc'" in sql

    def test_randomblob_vira_md5(self):
        sql = _traduzir("INSERT INTO indicacoes (chat_token) VALUES (lower(hex(randomblob(16))))")
        assert "randomblob" not in sql
        assert "md5(random()::text" in sql

    def test_like_vira_ilike(self):
        # No SQLite LIKE ignora maiusculas; no Postgres nao. Os contratos
        # prometem busca case-insensitive, entao a traducao usa ILIKE.
        assert _traduzir("SELECT 1 WHERE nome LIKE ?") == "SELECT 1 WHERE nome ILIKE %s"
        assert _traduzir("SELECT 1 WHERE a NOT LIKE ?") == "SELECT 1 WHERE a NOT ILIKE %s"

    def test_insert_ganha_returning_id(self):
        assert _traduzir("INSERT INTO clientes (nome) VALUES (?)").endswith("RETURNING id")

    def test_insert_em_tabela_sem_id_nao_ganha_returning(self):
        sql = _traduzir("INSERT INTO usuario_grupos (usuario_id, grupo_chave) VALUES (?, ?)")
        assert "RETURNING" not in sql

    def test_insert_que_ja_tem_returning_nao_duplica(self):
        sql = _traduzir("INSERT INTO clientes (nome) VALUES (?) RETURNING id")
        assert sql.lower().count("returning") == 1

    def test_select_nao_ganha_returning(self):
        assert "RETURNING" not in _traduzir("SELECT * FROM clientes")


class TestRow:
    """Row imita o sqlite3.Row: indice, nome e dict() precisam funcionar,
    porque o codigo das rotas usa os tres jeitos."""

    def linha(self):
        return Row((1, "Fulano"), ["id", "nome"])

    def test_acesso_por_indice(self):
        assert self.linha()[0] == 1

    def test_acesso_por_nome(self):
        assert self.linha()["nome"] == "Fulano"

    def test_converte_para_dict(self):
        assert dict(self.linha()) == {"id": 1, "nome": "Fulano"}

    def test_keys(self):
        assert self.linha().keys() == ["id", "nome"]


class TestConexao:
    def test_lastrowid_vem_do_returning(self, db):
        cur = db.execute("INSERT INTO clientes (tipo, nome) VALUES (?, ?)", ("PF", "Cliente X"))
        assert isinstance(cur.lastrowid, int) and cur.lastrowid > 0

    def test_count_por_indice(self, db):
        db.execute("INSERT INTO clientes (tipo, nome) VALUES ('PF', 'A')")
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 1

    def test_like_encontra_ignorando_maiusculas(self, db):
        db.execute("INSERT INTO clientes (tipo, nome) VALUES ('PF', 'Maria Silva')")
        db.commit()
        achados = db.execute("SELECT nome FROM clientes WHERE nome LIKE ?", ("%maria%",)).fetchall()
        assert [dict(r)["nome"] for r in achados] == ["Maria Silva"]

    def test_executemany(self, db):
        db.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES ('U', 'u@x.com', 'h')")
        db.commit()
        uid = db.execute("SELECT id FROM usuarios WHERE email = ?", ("u@x.com",)).fetchone()["id"]
        db.executemany(
            "INSERT INTO usuario_grupos (usuario_id, grupo_chave) VALUES (?, ?)",
            [(uid, "vendas"), (uid, "engenharia")],
        )
        db.commit()
        total = db.execute("SELECT COUNT(*) FROM usuario_grupos WHERE usuario_id = ?", (uid,)).fetchone()[0]
        assert total == 2

    def test_rollback_libera_transacao_abortada(self, db):
        db.execute("INSERT INTO clientes (tipo, nome) VALUES ('PF', 'A')")
        db.commit()
        try:
            db.execute("SELECT coluna_que_nao_existe FROM clientes")
        except Exception:
            db.rollback()
        # Sem o rollback, no Postgres qualquer query seguinte falharia.
        assert db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 1
