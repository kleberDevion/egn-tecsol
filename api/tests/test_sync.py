"""Sincronizacao com a Solarz: mapeamento de estagio -> status, leitura da
geracao (kWh) e o estorno quando o negocio regride de estagio."""

import pytest

from app.solarz import (
    PIPELINE_ENGENHARIA,
    PIPELINE_PRE_VENDAS,
    PIPELINE_PRE_VENDAS_IA,
    PIPELINE_VENDAS,
    STAGE_VENDAS_CONTRATO_ASSINADO,
)
from app.sync_indicacoes import (
    _estornar_comissao,
    _extrair_geracao,
    _mapear_status,
    _para_float,
    _proximo_nivel,
    _so_digitos,
)


class TestMapeamentoDeStatus:
    def test_funil_da_ia_e_pre_vendas_viram_em_atendimento(self):
        assert _mapear_status("OPEN", PIPELINE_PRE_VENDAS_IA, 63513) == "em_atendimento"
        assert _mapear_status("OPEN", PIPELINE_PRE_VENDAS, 42920) == "em_atendimento"

    def test_contrato_assinado_vira_fechado(self):
        assert _mapear_status("OPEN", PIPELINE_VENDAS, STAGE_VENDAS_CONTRATO_ASSINADO) == "fechado"

    def test_outros_estagios_de_vendas_viram_negociacao(self):
        assert _mapear_status("OPEN", PIPELINE_VENDAS, 42931) == "negociacao"

    def test_pipelines_pos_vendas_contam_como_fechado(self):
        assert _mapear_status("OPEN", PIPELINE_ENGENHARIA, 47217) == "fechado"

    def test_perdido_e_cancelado(self):
        assert _mapear_status("LOST", PIPELINE_VENDAS, 42931) == "perdido"
        assert _mapear_status("REJECTED", PIPELINE_VENDAS, 42931) == "cancelado"
        assert _mapear_status("DELETED", PIPELINE_VENDAS, 42931) == "cancelado"

    def test_perdido_ganha_de_qualquer_estagio(self):
        """Mesmo em Engenharia, um negocio LOST e perdido."""
        assert _mapear_status("LOST", PIPELINE_ENGENHARIA, 47217) == "perdido"


class TestTelefone:
    def test_tira_mascara(self):
        assert _so_digitos("(27) 98123-8061") == "27981238061"

    def test_valor_vazio(self):
        assert _so_digitos(None) == "" and _so_digitos("") == ""


class TestLeituraDaGeracao:
    def test_geracao_esperada_tem_prioridade(self):
        """O nome oficial do campo e "Geração esperada"; se os dois existirem,
        ele ganha do label generico."""
        campos = [
            {"label": "Geração do Sistema (kWh/mês):", "value": "350"},
            {"label": "Geração esperada", "value": "400"},
        ]
        assert _extrair_geracao(campos) == 400

    def test_aceita_o_label_que_existe_hoje(self):
        assert _extrair_geracao([{"label": "Geração do Sistema (kWh/mês):", "value": "400"}]) == 400

    def test_ignora_campo_que_nao_e_geracao(self):
        assert _extrair_geracao([{"label": "Consumo Atual:", "value": "600"}]) is None

    def test_ignora_geracao_vazia(self):
        assert _extrair_geracao([{"label": "Geração esperada", "value": None}]) is None

    def test_numero_com_unidade_e_virgula(self):
        assert _para_float("400 kWh") == 400
        assert _para_float("1.234,5") == 1234.5


class TestProgressaoDeNivel:
    @pytest.mark.parametrize(
        "nivel,vendas,esperado",
        [
            ("indicador", 0, "indicador"),
            ("indicador", 3, "apoiador"),
            ("indicador", 5, "parceiro"),
            ("apoiador", 3, "parceiro"),
            ("apoiador", 5, "embaixador"),
            ("indicador", 10, "elite"),
            ("elite", 20, "elite"),
        ],
    )
    def test_faixas(self, nivel, vendas, esperado):
        assert _proximo_nivel(nivel, vendas) == esperado


class TestEstorno:
    """Se o estagio regride na Solarz, o app precisa voltar ao estado anterior —
    inclusive desfazendo a comissao ja creditada."""

    def _venda_paga(self, db):
        from app.sync_indicacoes import _aplicar_comissao

        cur = db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao) VALUES ('B','b@x.com','h','TECSOL-B')"
        )
        b_id = cur.lastrowid
        cur = db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao, recrutado_por_id) VALUES ('A','a@x.com','h','TECSOL-A',?)",
            (b_id,),
        )
        a_id = cur.lastrowid
        cur = db.execute(
            "INSERT INTO indicacoes (indicador_id, nome_indicado, telefone_indicado, status) VALUES (?, 'Cliente', '279', 'fechado')",
            (a_id,),
        )
        indicacao_id = cur.lastrowid
        db.commit()
        _aplicar_comissao(db, indicacao_id, a_id, 400)
        db.commit()
        return a_id, b_id, indicacao_id

    def test_estorno_apaga_o_extrato(self, db):
        _, _, indicacao_id = self._venda_paga(db)
        # A cadeia aqui tem dois niveis (A indicou, B recrutou A), entao sao
        # dois lancamentos — o nivel 3 nao existe nesse cenario.
        assert db.execute("SELECT COUNT(*) FROM comissoes").fetchone()[0] == 2

        assert _estornar_comissao(db, indicacao_id) is True
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM comissoes").fetchone()[0] == 0

    def test_estorno_devolve_ganhos_e_vendas(self, db):
        a_id, b_id, indicacao_id = self._venda_paga(db)
        _estornar_comissao(db, indicacao_id)
        db.commit()

        a = dict(db.execute("SELECT total_ganhos, total_vendas FROM indicadores WHERE id = ?", (a_id,)).fetchone())
        b = dict(db.execute("SELECT total_ganhos, total_vendas FROM indicadores WHERE id = ?", (b_id,)).fetchone())
        assert a["total_ganhos"] == pytest.approx(0.0)
        assert a["total_vendas"] == 0
        assert b["total_ganhos"] == pytest.approx(0.0)

    def test_estorno_sem_comissao_nao_faz_nada(self, db):
        cur = db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao) VALUES ('X','x@x.com','h','TECSOL-X')"
        )
        cur = db.execute(
            "INSERT INTO indicacoes (indicador_id, nome_indicado, telefone_indicado) VALUES (?, 'C', '279')",
            (cur.lastrowid,),
        )
        db.commit()
        assert _estornar_comissao(db, cur.lastrowid) is False

    def test_totais_nao_ficam_negativos(self, db):
        """Estornar duas vezes (ou dado inconsistente) nao pode zerar abaixo de 0."""
        a_id, _, indicacao_id = self._venda_paga(db)
        _estornar_comissao(db, indicacao_id)
        db.commit()
        _estornar_comissao(db, indicacao_id)
        db.commit()
        a = dict(db.execute("SELECT total_ganhos, total_vendas FROM indicadores WHERE id = ?", (a_id,)).fetchone())
        assert a["total_ganhos"] >= 0 and a["total_vendas"] >= 0


class TestSincronizacaoCompleta:
    """A sincronizacao olha TODAS as indicacoes, nao so as abertas — senao um
    card fechado ficaria travado quando o negocio regride na Solarz."""

    def _cenario(self, db, monkeypatch, pipeline_id, stage_id, status_deal="OPEN"):
        import app.sync_indicacoes as sync

        cur = db.execute(
            "INSERT INTO indicadores (nome, email, senha_hash, codigo_indicacao) VALUES ('A','a@x.com','h','TECSOL-A')"
        )
        ind_id = cur.lastrowid
        cur = db.execute(
            "INSERT INTO indicacoes (indicador_id, nome_indicado, telefone_indicado, status) VALUES (?, 'Cliente', '27981238061', 'fechado')",
            (ind_id,),
        )
        indicacao_id = cur.lastrowid
        db.commit()

        monkeypatch.setattr(sync, "buscar_pessoa_por_telefone", lambda tel: {"id": 55})
        monkeypatch.setattr(
            sync,
            "_carregar_negocios_por_pessoa",
            lambda: {
                55: {
                    "id": 777,
                    "status": status_deal,
                    "pipelineId": pipeline_id,
                    "pipelineStageId": stage_id,
                    "value": 21500,
                }
            },
        )
        monkeypatch.setattr(sync, "_carregar_geracao", lambda: ({}, {}))
        return indicacao_id

    def test_regressao_volta_o_status(self, db, monkeypatch):
        from app.sync_indicacoes import sincronizar

        indicacao_id = self._cenario(db, monkeypatch, PIPELINE_VENDAS, 42931)  # Visita/Proposta
        sincronizar(db)

        atual = dict(db.execute("SELECT status FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone())
        assert atual["status"] == "negociacao"

    def test_regressao_estorna_a_comissao(self, db, monkeypatch):
        from app.sync_indicacoes import _aplicar_comissao, sincronizar

        indicacao_id = self._cenario(db, monkeypatch, PIPELINE_VENDAS, 42931)
        ind_id = dict(db.execute("SELECT indicador_id FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone())[
            "indicador_id"
        ]
        _aplicar_comissao(db, indicacao_id, ind_id, 400)
        db.execute("UPDATE indicacoes SET comissao_gerada = 160 WHERE id = ?", (indicacao_id,))
        db.commit()

        sincronizar(db)

        assert db.execute("SELECT COUNT(*) FROM comissoes").fetchone()[0] == 0
        linha = dict(
            db.execute("SELECT status, comissao_gerada, valor_sistema FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone()
        )
        assert linha["status"] == "negociacao"
        assert linha["comissao_gerada"] is None
        assert linha["valor_sistema"] is None

    def test_negocio_perdido_marca_perdido(self, db, monkeypatch):
        from app.sync_indicacoes import sincronizar

        indicacao_id = self._cenario(db, monkeypatch, PIPELINE_VENDAS, 42931, status_deal="LOST")
        sincronizar(db)
        atual = dict(db.execute("SELECT status FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone())
        assert atual["status"] == "perdido"

    def test_continua_fechado_quando_nao_regride(self, db, monkeypatch):
        from app.sync_indicacoes import sincronizar

        indicacao_id = self._cenario(db, monkeypatch, PIPELINE_VENDAS, STAGE_VENDAS_CONTRATO_ASSINADO)
        sincronizar(db)
        linha = dict(
            db.execute("SELECT status, valor_sistema FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone()
        )
        assert linha["status"] == "fechado"
        assert linha["valor_sistema"] == pytest.approx(21500)
