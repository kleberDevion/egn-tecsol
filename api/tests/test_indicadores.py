"""App de indicacoes: cadastro, login, indicacoes, rede de recrutamento e
comissao multi-nivel."""

import pytest


class TestAutenticacao:
    def test_signup_cria_indicador_com_codigo(self, client):
        resp = client.post(
            "/api/v1/indicadores/auth/signup",
            json={"nome": "Fulano", "email": "f@x.com", "senha": "senha12345"},
        )
        assert resp.status_code == 201
        dados = resp.get_json()
        assert dados["codigo_indicacao"].startswith("TECSOL-")
        assert dados["total_ganhos"] == 0

    def test_signup_com_email_repetido_da_409(self, client):
        corpo = {"nome": "Fulano", "email": "f@x.com", "senha": "senha12345"}
        client.post("/api/v1/indicadores/auth/signup", json=corpo)
        resp = client.post("/api/v1/indicadores/auth/signup", json=corpo)
        assert resp.status_code == 409

    def test_signup_com_senha_curta_da_400(self, client):
        resp = client.post(
            "/api/v1/indicadores/auth/signup",
            json={"nome": "Fulano", "email": "f2@x.com", "senha": "123"},
        )
        assert resp.status_code == 400

    def test_login_e_me(self, client, indicador):
        c, dados = indicador
        resp = c.get("/api/v1/indicadores/me")
        assert resp.status_code == 200
        assert resp.get_json()["email"] == dados["email"]

    def test_me_sem_sessao_da_401(self, client):
        assert client.get("/api/v1/indicadores/me").status_code == 401

    def test_login_com_senha_errada_da_401(self, client, indicador):
        c, dados = indicador
        resp = c.post("/api/v1/indicadores/auth/login", json={"email": dados["email"], "senha": "errada123"})
        assert resp.status_code == 401


class TestConviteDeRecrutamento:
    def test_signup_com_convite_vincula_a_rede(self, client, indicador):
        _, recrutador = indicador
        resp = client.post(
            "/api/v1/indicadores/auth/signup",
            json={
                "nome": "Recrutado",
                "email": "rec@x.com",
                "senha": "senha12345",
                "codigo_convite": recrutador["codigo_indicacao"],
            },
        )
        assert resp.status_code == 201
        assert resp.get_json()["recrutado_por_id"] == recrutador["id"]

    def test_convite_invalido_nao_impede_cadastro(self, client):
        resp = client.post(
            "/api/v1/indicadores/auth/signup",
            json={"nome": "Sem Rede", "email": "sr@x.com", "senha": "senha12345", "codigo_convite": "NAO-EXISTE"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["recrutado_por_id"] is None


class TestIndicacoes:
    def test_criar_indicacao_manda_pro_funil_pre_vendas(self, indicador, solarz_falso):
        from app.solarz import PIPELINE_PRE_VENDAS, STAGE_PRE_VENDAS_PROSPECT

        c, _ = indicador
        resp = c.post(
            "/api/v1/indicadores/indicacoes",
            json={"nome_indicado": "Cliente A", "telefone_indicado": "27988887777"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["status"] == "recebido"

        enviado = solarz_falso["negocios"][-1]
        assert enviado["pipeline_id"] == PIPELINE_PRE_VENDAS
        assert enviado["pipeline_stage_id"] == STAGE_PRE_VENDAS_PROSPECT

    def test_indicacao_sem_telefone_da_400(self, indicador, solarz_falso):
        c, _ = indicador
        resp = c.post("/api/v1/indicadores/indicacoes", json={"nome_indicado": "Sem Telefone"})
        assert resp.status_code == 400

    def test_indicador_nao_pode_marcar_como_fechado(self, indicador, solarz_falso):
        c, _ = indicador
        criada = c.post(
            "/api/v1/indicadores/indicacoes",
            json={"nome_indicado": "Cliente B", "telefone_indicado": "27988887777"},
        ).get_json()
        resp = c.patch(f"/api/v1/indicadores/indicacoes/{criada['id']}", json={"status": "fechado"})
        assert resp.status_code == 400

    def test_indicador_atualiza_status_permitido(self, indicador, solarz_falso):
        c, _ = indicador
        criada = c.post(
            "/api/v1/indicadores/indicacoes",
            json={"nome_indicado": "Cliente C", "telefone_indicado": "27988887777"},
        ).get_json()
        resp = c.patch(f"/api/v1/indicadores/indicacoes/{criada['id']}", json={"status": "negociacao"})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "negociacao"

    def test_so_ve_as_proprias_indicacoes(self, client, indicador, solarz_falso):
        c, _ = indicador
        c.post(
            "/api/v1/indicadores/indicacoes",
            json={"nome_indicado": "Do Primeiro", "telefone_indicado": "27911112222"},
        )
        c.post("/api/v1/indicadores/auth/logout")
        c.post(
            "/api/v1/indicadores/auth/signup",
            json={"nome": "Outro", "email": "outro@x.com", "senha": "senha12345"},
        )
        listagem = c.get("/api/v1/indicadores/minhas-indicacoes").get_json()
        assert listagem["data"] == []


class TestLinkPublico:
    def test_acesso_ao_link_conta_clique(self, client, indicador):
        c, dados = indicador
        codigo = dados["codigo_indicacao"]
        for _ in range(3):
            assert client.get(f"/api/v1/publico/indicadores/{codigo}").status_code == 200
        assert c.get("/api/v1/indicadores/me").get_json()["total_cliques"] == 3

    def test_link_inexistente_da_404(self, client):
        assert client.get("/api/v1/publico/indicadores/NAO-EXISTE").status_code == 404

    def test_form_publico_cai_no_funil_da_ia(self, client, indicador, solarz_falso):
        from app.solarz import PIPELINE_PRE_VENDAS_IA, STAGE_PRE_VENDAS_IA_TRIAGEM

        _, dados = indicador
        resp = client.post(
            f"/api/v1/publico/indicadores/{dados['codigo_indicacao']}/indicacoes",
            json={"nome_indicado": "Veio do Link", "telefone_indicado": "27977776666"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["indicador_id"] == dados["id"]

        enviado = solarz_falso["negocios"][-1]
        assert enviado["pipeline_id"] == PIPELINE_PRE_VENDAS_IA
        assert enviado["pipeline_stage_id"] == STAGE_PRE_VENDAS_IA_TRIAGEM


class TestComissaoMultiNivel:
    """A regra do dono: R$/kWh de geracao, pagos em tres niveis da cadeia de
    recrutamento (0.40 / 0.15 / 0.075 por padrao)."""

    def _cadeia(self, db):
        """C recrutou B, B recrutou A. A indica o cliente."""
        ids = {}
        for nome, recrutador in (("C", None), ("B", "C"), ("A", "B")):
            cur = db.execute(
                """INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao, recrutado_por_id)
                   VALUES (?, ?, 'h', ?, ?)""",
                (nome, f"{nome}@x.com", f"TECSOL-{nome}", ids.get(recrutador)),
            )
            ids[nome] = cur.lastrowid
        cur = db.execute(
            "INSERT INTO indicacoes (indicador_id, nome_indicado, telefone_indicado, status) VALUES (?, ?, ?, 'fechado')",
            (ids["A"], "Cliente Fechado", "27900001111"),
        )
        db.commit()
        return ids, cur.lastrowid

    def test_paga_os_tres_niveis(self, db):
        from app.sync_indicacoes import _aplicar_comissao

        ids, indicacao_id = self._cadeia(db)
        valor_n1 = _aplicar_comissao(db, indicacao_id, ids["A"], 400)
        db.commit()

        assert valor_n1 == pytest.approx(160.0)  # 400 * 0.40
        extrato = {
            dict(r)["indicador_id"]: dict(r)
            for r in db.execute("SELECT indicador_id, nivel, valor FROM comissoes")
        }
        assert extrato[ids["A"]]["nivel"] == 1 and extrato[ids["A"]]["valor"] == pytest.approx(160.0)
        assert extrato[ids["B"]]["nivel"] == 2 and extrato[ids["B"]]["valor"] == pytest.approx(60.0)
        assert extrato[ids["C"]]["nivel"] == 3 and extrato[ids["C"]]["valor"] == pytest.approx(30.0)

    def test_venda_conta_so_para_o_nivel_1(self, db):
        from app.sync_indicacoes import _aplicar_comissao

        ids, indicacao_id = self._cadeia(db)
        _aplicar_comissao(db, indicacao_id, ids["A"], 400)
        db.commit()

        vendas = {
            dict(r)["id"]: dict(r)["total_vendas"]
            for r in db.execute("SELECT id, total_vendas FROM indicadores")
        }
        assert vendas[ids["A"]] == 1
        assert vendas[ids["B"]] == 0 and vendas[ids["C"]] == 0

    def test_nao_paga_duas_vezes_a_mesma_indicacao(self, db):
        from app.sync_indicacoes import _aplicar_comissao

        ids, indicacao_id = self._cadeia(db)
        _aplicar_comissao(db, indicacao_id, ids["A"], 400)
        db.commit()
        assert _aplicar_comissao(db, indicacao_id, ids["A"], 400) is None
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM comissoes").fetchone()[0] == 3

    def test_cadeia_curta_paga_so_quem_existe(self, db):
        """Indicador sem recrutador: so o nivel 1 recebe."""
        from app.sync_indicacoes import _aplicar_comissao

        cur = db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao) VALUES ('Sozinho', 's@x.com', 'h', 'TECSOL-S')"
        )
        sozinho = cur.lastrowid
        cur = db.execute(
            "INSERT INTO indicacoes (indicador_id, nome_indicado, telefone_indicado, status) VALUES (?, 'C', '279', 'fechado')",
            (sozinho,),
        )
        db.commit()
        _aplicar_comissao(db, cur.lastrowid, sozinho, 100)
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM comissoes").fetchone()[0] == 1

    def test_extrato_inclui_ganhos_da_rede(self, client, db):
        """Quem recebe como nivel 2 ve a comissao, mesmo a indicacao sendo de outro."""
        from app.auth import hash_password
        from app.sync_indicacoes import _aplicar_comissao

        db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao) VALUES ('B', 'b@x.com', ?, 'TECSOL-B')",
            (hash_password("senha12345"),),
        )
        b_id = db.execute("SELECT id FROM indicadores WHERE email = 'b@x.com'").fetchone()["id"]
        cur = db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao, recrutado_por_id) VALUES ('A', 'a@x.com', 'h', 'TECSOL-A', ?)",
            (b_id,),
        )
        a_id = cur.lastrowid
        cur = db.execute(
            "INSERT INTO indicacoes (indicador_id, nome_indicado, telefone_indicado, status) VALUES (?, 'Cliente', '279', 'fechado')",
            (a_id,),
        )
        db.commit()
        _aplicar_comissao(db, cur.lastrowid, a_id, 400)
        db.commit()

        client.post("/api/v1/indicadores/auth/login", json={"email": "b@x.com", "senha": "senha12345"})
        extrato = client.get("/api/v1/indicadores/minhas-comissoes").get_json()["data"]
        assert len(extrato) == 1
        assert extrato[0]["nivel"] == 2
        assert extrato[0]["valor"] == pytest.approx(60.0)

        rede = client.get("/api/v1/indicadores/minha-rede").get_json()
        assert [m["nome"] for m in rede["nivel_2"]] == ["A"]
