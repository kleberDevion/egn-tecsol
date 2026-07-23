"""Leads que nao vem de indicador: site institucional e Google Ads.

Os dois caem no funil "Comercial - Pre-vendas" e ficam FORA da tabela
`indicacoes` de proposito — nao pertencem a ninguem e nao geram comissao.
"""


class TestLeadDoSite:
    def test_cria_lead_e_negocio_no_funil_pre_vendas(self, client, db, solarz_falso):
        from app.solarz import PIPELINE_PRE_VENDAS, STAGE_PRE_VENDAS_PROSPECT

        resp = client.post(
            "/api/v1/publico/leads-site",
            json={
                "nome": "Visitante do Site",
                "telefone": "(27) 98888-7777",
                "email": "v@x.com",
                "cidade": "Linhares",
                "tipo_solucao": "Residencial",
                "origem": "hero",
            },
        )
        assert resp.status_code == 201

        enviado = solarz_falso["negocios"][-1]
        assert enviado["pipeline_id"] == PIPELINE_PRE_VENDAS
        assert enviado["pipeline_stage_id"] == STAGE_PRE_VENDAS_PROSPECT

        lead = dict(db.execute("SELECT * FROM leads_site").fetchone())
        assert lead["nome"] == "Visitante do Site"
        assert lead["cidade"] == "Linhares"
        assert lead["solarz_deal_id"] == solarz_falso["deal_id"]

    def test_nao_entra_na_tabela_de_indicacoes(self, client, db, solarz_falso):
        client.post(
            "/api/v1/publico/leads-site",
            json={"nome": "Visitante", "telefone": "27988887777"},
        )
        assert db.execute("SELECT COUNT(*) FROM indicacoes").fetchone()[0] == 0

    def test_sem_nome_da_400(self, client, solarz_falso):
        resp = client.post("/api/v1/publico/leads-site", json={"telefone": "27988887777"})
        assert resp.status_code == 400

    def test_sem_telefone_da_400(self, client, solarz_falso):
        resp = client.post("/api/v1/publico/leads-site", json={"nome": "Sem Telefone"})
        assert resp.status_code == 400

    def test_lead_salvo_mesmo_se_a_solarz_falhar(self, client, db, monkeypatch):
        """A Solarz cair nao pode fazer a Tecsol perder o lead."""
        import app.routes.leads_site as site
        from app.solarz import SolarzApiError

        def explode(**kwargs):
            raise SolarzApiError("Solarz fora do ar")

        monkeypatch.setattr(site, "criar_negocio", explode)

        resp = client.post(
            "/api/v1/publico/leads-site", json={"nome": "Salvo Mesmo Assim", "telefone": "27900001111"}
        )
        assert resp.status_code == 201
        lead = dict(db.execute("SELECT * FROM leads_site").fetchone())
        assert lead["nome"] == "Salvo Mesmo Assim"
        assert lead["solarz_deal_id"] is None


class TestWebhookGoogleAds:
    URL = "/api/v1/publico/leads-google"
    CHAVE = "chave-de-teste"

    def test_chave_errada_da_401(self, client):
        assert client.post(self.URL, json={"key": "errada"}).status_code == 401

    def test_sem_chave_da_401(self, client):
        assert client.post(self.URL, json={}).status_code == 401

    def test_lead_de_teste_do_google_nao_vira_registro(self, client, db):
        """O Google manda um lead de teste ao salvar o formulario: precisa
        responder 200 pra validar a URL, mas nao pode sujar a base."""
        resp = client.post(self.URL, json={"key": self.CHAVE, "is_test": True, "lead_id": "x"})
        assert resp.status_code == 200
        assert resp.get_json()["teste"] is True
        assert db.execute("SELECT COUNT(*) FROM leads_site").fetchone()[0] == 0

    def test_lead_real_vira_negocio(self, client, db, solarz_falso):
        from app.solarz import PIPELINE_PRE_VENDAS

        resp = client.post(
            self.URL,
            json={
                "key": self.CHAVE,
                "lead_id": "abc",
                "campaign_id": 123,
                "user_column_data": [
                    {"column_id": "FULL_NAME", "string_value": "Lead do Ads"},
                    {"column_id": "PHONE_NUMBER", "string_value": "+5527966665555"},
                    {"column_id": "EMAIL", "string_value": "ads@x.com"},
                ],
            },
        )
        assert resp.status_code == 200

        lead = dict(db.execute("SELECT * FROM leads_site").fetchone())
        assert lead["nome"] == "Lead do Ads"
        assert lead["origem"] == "google_ads"
        assert lead["pagina"] == "campanha:123"
        assert solarz_falso["negocios"][-1]["pipeline_id"] == PIPELINE_PRE_VENDAS

    def test_lead_sem_telefone_da_400(self, client, solarz_falso):
        resp = client.post(
            self.URL,
            json={
                "key": self.CHAVE,
                "user_column_data": [{"column_id": "FULL_NAME", "string_value": "So Nome"}],
            },
        )
        assert resp.status_code == 400
