"""Rotas do CRM interno: usuarios, chat de suporte, niveis de comissao e a
tela de geracao de documentos. Cobre tambem os bugs de dialeto que apareceram
na migracao pro PostgreSQL."""


class TestUsuarios:
    def test_cria_usuario_com_grupos(self, admin):
        """Regressao: `executemany` nao existia na camada de compatibilidade,
        entao criar usuario com grupo dava 500."""
        resp = admin.post(
            "/api/v1/usuarios",
            json={
                "nome": "Operador Teste",
                "email": "op@teste.com",
                "senha": "senha12345",
                "papel": "operador",
                "grupos": ["vendas", "engenharia"],
            },
        )
        assert resp.status_code == 201
        assert sorted(resp.get_json()["grupos"]) == ["engenharia", "vendas"]

    def test_cria_usuario_sem_grupo(self, admin):
        resp = admin.post(
            "/api/v1/usuarios",
            json={"nome": "Sem Grupo", "email": "sg@teste.com", "senha": "senha12345", "papel": "operador", "grupos": []},
        )
        assert resp.status_code == 201
        assert resp.get_json()["grupos"] == []

    def test_email_repetido_da_409(self, admin):
        corpo = {
            "nome": "Dup",
            "email": "dup@teste.com",
            "senha": "senha12345",
            "papel": "operador",
            "grupos": [],
        }
        admin.post("/api/v1/usuarios", json=corpo)
        assert admin.post("/api/v1/usuarios", json=corpo).status_code == 409

    def test_exige_login(self, client):
        assert client.post("/api/v1/usuarios", json={}).status_code == 401


class TestSuporte:
    def test_inbox_do_admin(self, admin):
        """Regressao: a query usava um apelido de coluna dentro de COALESCE no
        ORDER BY — o SQLite aceita, o PostgreSQL nao (dava 500 ao abrir o chat)."""
        resp = admin.get("/api/v1/suporte/threads")
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []

    def test_inbox_ordena_pela_ultima_mensagem(self, admin, db):
        from app.auth import hash_password

        db.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, papel) VALUES ('Op','op2@x.com',?, 'operador')",
            (hash_password("senha12345"),),
        )
        op_id = db.execute("SELECT id FROM usuarios WHERE email = 'op2@x.com'").fetchone()["id"]
        for i in (1, 2):
            cur = db.execute("INSERT INTO suporte_threads (usuario_id) VALUES (?)", (op_id,))
            db.execute(
                "INSERT INTO suporte_mensagens (thread_id, autor_usuario_id, texto, criado_em) VALUES (?, ?, ?, ?)",
                (cur.lastrowid, op_id, f"msg {i}", f"2026-07-0{i}T10:00:00Z"),
            )
        db.commit()

        dados = admin.get("/api/v1/suporte/threads").get_json()["data"]
        assert len(dados) == 2
        assert dados[0]["ultima_mensagem"] == "msg 2"  # mais recente primeiro

    def test_admin_nao_tem_conversa_propria(self, admin):
        assert admin.get("/api/v1/suporte/minha-thread").status_code == 400

    def test_operador_nao_ve_inbox(self, client, db):
        from app.auth import hash_password

        db.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, papel) VALUES ('Op','op3@x.com',?, 'operador')",
            (hash_password("senha12345"),),
        )
        db.commit()
        client.post("/api/v1/auth/login", json={"email": "op3@x.com", "senha": "senha12345"})
        assert client.get("/api/v1/suporte/threads").status_code == 403


class TestNiveisDeComissao:
    def test_valores_padrao(self, client):
        dados = client.get("/api/v1/niveis/comissao").get_json()["data"]
        assert [(d["nivel"], d["valor_por_kwh"]) for d in dados] == [(1, 0.40), (2, 0.15), (3, 0.075)]

    def test_admin_altera_valor(self, admin):
        resp = admin.patch("/api/v1/niveis/comissao/1", json={"valor_por_kwh": 0.5})
        assert resp.status_code == 200
        assert resp.get_json()["valor_por_kwh"] == 0.5

    def test_valor_negativo_da_400(self, admin):
        assert admin.patch("/api/v1/niveis/comissao/1", json={"valor_por_kwh": -1}).status_code == 400

    def test_valor_nao_numerico_da_400(self, admin):
        assert admin.patch("/api/v1/niveis/comissao/1", json={"valor_por_kwh": "muito"}).status_code == 400

    def test_nivel_inexistente_da_404(self, admin):
        assert admin.patch("/api/v1/niveis/comissao/9", json={"valor_por_kwh": 1}).status_code == 404

    def test_sem_login_nao_altera(self, client):
        assert client.patch("/api/v1/niveis/comissao/1", json={"valor_por_kwh": 1}).status_code == 401

    def test_novo_valor_e_usado_no_calculo(self, admin, db):
        """Alterar no painel muda a comissao das proximas vendas."""
        from app.sync_indicacoes import _aplicar_comissao

        admin.patch("/api/v1/niveis/comissao/1", json={"valor_por_kwh": 1.0})

        cur = db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao) VALUES ('A','a2@x.com','h','TECSOL-A2')"
        )
        ind_id = cur.lastrowid
        cur = db.execute(
            "INSERT INTO indicacoes (indicador_id, nome_indicado, telefone_indicado, status) VALUES (?, 'C','279','fechado')",
            (ind_id,),
        )
        db.commit()
        assert _aplicar_comissao(db, cur.lastrowid, ind_id, 100) == 100.0


class TestGeracaoDocumentosRotas:
    def test_listagem_vazia(self, admin):
        assert admin.get("/api/v1/geracao-documentos").get_json()["data"] == []

    def test_exige_login(self, client):
        assert client.get("/api/v1/geracao-documentos").status_code == 401
        assert client.get("/api/v1/geracao-documentos/pendentes").status_code == 401

    def test_detalhe_inexistente_da_404(self, admin):
        assert admin.get("/api/v1/geracao-documentos/999").status_code == 404

    def test_listagem_traz_nome_do_cliente(self, admin, db):
        cur = db.execute("INSERT INTO clientes (tipo, nome) VALUES ('PF', 'Fulano de Tal')")
        db.execute(
            """INSERT INTO geracoes_documentos (solarz_deal_id, numero_pedido, numero_cft, cliente_id, status)
               VALUES (1, '01', 'CFT1', ?, 'pronto')""",
            (cur.lastrowid,),
        )
        db.commit()
        dados = admin.get("/api/v1/geracao-documentos").get_json()["data"]
        assert dados[0]["cliente_nome"] == "Fulano de Tal"


class TestCors:
    def test_reflete_origem_quando_nao_ha_whitelist(self, client):
        resp = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
        assert resp.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_bloqueia_origem_fora_da_whitelist(self, client, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "https://crm.tecsol.com.br")
        resp = client.get("/api/v1/health", headers={"Origin": "https://site-malicioso.com"})
        assert resp.headers.get("Access-Control-Allow-Origin") is None

    def test_permite_origem_da_whitelist(self, client, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "https://crm.tecsol.com.br")
        resp = client.get("/api/v1/health", headers={"Origin": "https://crm.tecsol.com.br"})
        assert resp.headers.get("Access-Control-Allow-Origin") == "https://crm.tecsol.com.br"


class TestHealth:
    def test_health(self, client):
        assert client.get("/api/v1/health").get_json() == {"status": "ok"}


class TestFotoDePerfil:
    """A foto fica no banco, nao em disco: a hospedagem apaga o disco a cada
    deploy, e a foto sumia sem deixar rastro."""

    def _png(self):
        # PNG 1x1 valido, menor arquivo possivel
        import base64

        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )

    def _enviar(self, client, nome="foto.png", conteudo=None):
        import io

        return client.post(
            "/api/v1/auth/foto",
            data={"foto": (io.BytesIO(conteudo if conteudo is not None else self._png()), nome)},
            content_type="multipart/form-data",
        )

    def test_upload_guarda_no_banco(self, admin, db):
        resp = self._enviar(admin)
        assert resp.status_code == 200
        assert resp.get_json()["foto_url"] is not None

        linha = dict(db.execute("SELECT foto_bytes, foto_tipo FROM usuarios WHERE email = 'admin@teste.com'").fetchone())
        assert linha["foto_bytes"] is not None
        assert linha["foto_tipo"] == "image/png"

    def test_download_devolve_a_imagem(self, admin, db):
        self._enviar(admin)
        uid = db.execute("SELECT id FROM usuarios WHERE email = 'admin@teste.com'").fetchone()["id"]

        resp = admin.get(f"/api/v1/auth/foto/{uid}")
        assert resp.status_code == 200
        assert resp.mimetype == "image/png"
        assert resp.data == self._png()

    def test_formato_invalido_recusado(self, admin):
        assert self._enviar(admin, nome="virus.exe").status_code == 400

    def test_arquivo_grande_recusado(self, admin):
        grande = b"\x89PNG" + b"0" * (4 * 1024 * 1024)
        assert self._enviar(admin, conteudo=grande).status_code == 400

    def test_usuario_sem_foto_da_404(self, admin, db):
        uid = db.execute("SELECT id FROM usuarios WHERE email = 'admin@teste.com'").fetchone()["id"]
        assert admin.get(f"/api/v1/auth/foto/{uid}").status_code == 404

    def test_foto_exige_login(self, client):
        assert client.get("/api/v1/auth/foto/1").status_code == 401
