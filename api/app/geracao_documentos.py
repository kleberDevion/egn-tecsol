"""Orquestra a geração de documentos de um negócio da Solarz.

Fluxo 100% pull: ninguém envia dados pra cá. A partir do `solarz_deal_id` a
gente busca o negócio (pessoa, valores, campos customizados) e a proposta,
monta o contexto e preenche os modelos .docx.

Regra de cliente (definida pelo dono): o trabalho da Tecsol não é recorrente —
se já existe cliente com o mesmo nome + CPF, não cria outro, só pendura mais um
projeto/contrato no registro existente.
"""

import json
import logging
import re
from datetime import datetime, timezone

from app.documentos_gerador import gerar
from app.solarz import (
    PIPELINE_VENDAS,
    STAGE_VENDAS_GERAR_DOCUMENTACAO,
    buscar_negocio,
    listar_negocios,
    listar_propostas,
)

logger = logging.getLogger(__name__)

# Constantes da Tecsol usadas nos documentos (não vêm da Solarz).
RESPONSAVEL_TECNICO = {
    "nome": "William Couto Pereira",
    "registro": "10694446777",
    "projetista": "William Couto Pereira",
}


def _campo(deal, *nomes):
    """Lê um campo customizado do negócio pelo label (case-insensitive)."""
    for campo in deal.get("dealCustomFieldValues") or []:
        label = (campo.get("label") or "").strip().lower().rstrip(":")
        for nome in nomes:
            if label == nome.strip().lower().rstrip(":"):
                return campo.get("value")
    return None


def _texto(valor):
    """Alguns campos custom da Solarz vêm como JSON (ex: Forma de Pagamento
    chega `["À Vista - Pix"]`). Devolve texto legível pro documento."""
    if valor in (None, ""):
        return None
    texto = str(valor).strip()
    if texto.startswith("["):
        try:
            itens = json.loads(texto)
            if isinstance(itens, list):
                return ", ".join(str(i) for i in itens)
        except json.JSONDecodeError:
            pass
    return texto


def _numero(valor):
    if valor in (None, ""):
        return None
    m = re.search(r"\d[\d.,]*", str(valor))
    if not m:
        return None
    n = m.group()
    if "," in n:
        n = n.replace(".", "").replace(",", ".")
    try:
        return float(n)
    except ValueError:
        return None


def listar_pendentes():
    """Negócios parados no estágio "Gerar Documentação" — viram os cards da tela."""
    pendentes, page = [], 0
    while True:
        data = listar_negocios(page=page, size=100, pipeline_id=PIPELINE_VENDAS)
        for deal in data.get("content", []):
            if deal.get("pipelineStageId") == STAGE_VENDAS_GERAR_DOCUMENTACAO:
                pendentes.append(deal)
        if data.get("last", True):
            break
        page += 1
    return pendentes


def _proposta_do_deal(deal_id, person_id):
    """Proposta mais recente do negócio (ou da pessoa, quando a proposta não
    está vinculada ao negócio)."""
    melhor, page = None, 0
    while True:
        data = listar_propostas(page=page, size=100)
        for prop in data.get("content", []):
            if prop.get("dealId") == deal_id or (person_id and prop.get("personId") == person_id):
                if melhor is None or (prop.get("creationDate") or "") > (melhor.get("creationDate") or ""):
                    melhor = prop
        if data.get("last", True):
            break
        page += 1
    return melhor


def montar_contexto(deal_id, numero_pedido, numero_cft):
    """Busca tudo na Solarz e monta o dicionário que alimenta os modelos."""
    deal = buscar_negocio(deal_id)
    pessoa = deal.get("person") or {}
    endereco = pessoa.get("address") or {}
    cidade = (endereco.get("city") or {}) if isinstance(endereco.get("city"), dict) else {}
    provincia = (endereco.get("province") or {}) if isinstance(endereco.get("province"), dict) else {}
    proposta = _proposta_do_deal(deal_id, pessoa.get("id"))

    ano = datetime.now(timezone.utc).year
    seq = (numero_pedido or "").strip() or str(deal_id)
    doc_tecsol = f"{ano}-{seq}-750-001-A"

    potencia = _numero(_campo(deal, "Potência em kWp")) or (proposta or {}).get("equipmentFullPower")

    return {
        "data": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        "numero_pedido": seq,
        "numero_cft": numero_cft,
        "doc_tecsol": doc_tecsol,
        "codigo_projeto": f"PJ-{doc_tecsol}",
        "codigo_contrato": f"CT-{doc_tecsol}",
        "codigo_memorial": f"MD-{doc_tecsol}",
        "codigo_desenho": f"DE-{doc_tecsol}",
        "cliente": {
            "nome": pessoa.get("name"),
            "cpf": pessoa.get("identifier"),
            "telefone": pessoa.get("phone"),
            "email": pessoa.get("email"),
            "endereco": endereco.get("formattedAddress") or endereco.get("street"),
            "cep": endereco.get("zipCode"),
            "cidade": cidade.get("name"),
            "uf": provincia.get("uf"),
            "latitude": endereco.get("latitude"),
            "longitude": endereco.get("longitude"),
            "numero_instalacao": _campo(deal, "Número da instalação", "UC"),
        },
        "sistema": {
            "potencia_kwp": potencia,
            "potencia_kw": None,
            "geracao_kwh_mes": _numero(_campo(deal, "Geração esperada", "Geração do Sistema")),
            "valor_conta": _numero(_campo(deal, "Consumo Atual")),
        },
        # Equipamentos ainda não são expostos pela API da Solarz (ver
        # contracts/campos_faltantes_solarz.json). Ficam vazios até lá.
        "modulos": {},
        "inversor": {},
        "comercial": {
            "valor_projeto": deal.get("value"),
            "valor_kit": _numero(_campo(deal, "Valor do KIT")),
            "forma_pagamento": _texto(_campo(deal, "Forma de Pagamento")),
            "fornecedor": None,
            "estrutura": None,
        },
        "responsavel_tecnico": RESPONSAVEL_TECNICO,
    }


def _cliente_id(db, nome, cpf):
    """Reaproveita o cliente quando nome + CPF batem; senão cria."""
    if not nome:
        return None
    if cpf:
        row = db.execute(
            "SELECT id FROM clientes WHERE nome = ? AND cpf_cnpj = ?", (nome, cpf)
        ).fetchone()
    else:
        row = db.execute("SELECT id FROM clientes WHERE nome = ? AND cpf_cnpj IS NULL", (nome,)).fetchone()
    if row is not None:
        return row["id"]
    cur = db.execute(
        "INSERT INTO clientes (tipo, nome, cpf_cnpj) VALUES (?, ?, ?)",
        ("PF", nome, cpf),
    )
    return cur.lastrowid


def executar(db, geracao_id, dir_modelos):
    """Roda a geração (chamado pelo worker) e atualiza a linha em
    `geracoes_documentos` com o resultado.

    Os arquivos NÃO são salvos em disco: o que fica guardado é o `contexto`
    (JSON com todos os dados do projeto). No download os .docx são remontados
    a partir dele — assim funciona em qualquer hospedagem, mesmo com disco
    efêmero ou com o worker rodando em outra máquina."""
    linha = db.execute("SELECT * FROM geracoes_documentos WHERE id = ?", (geracao_id,)).fetchone()
    if linha is None:
        raise ValueError(f"Geração {geracao_id} não encontrada")

    try:
        ctx = montar_contexto(linha["solarz_deal_id"], linha["numero_pedido"], linha["numero_cft"])
        cliente = ctx["cliente"]
        cliente_id = _cliente_id(db, cliente["nome"], cliente["cpf"])

        codigo = ctx["codigo_projeto"]
        projeto = db.execute("SELECT id FROM projetos WHERE codigo = ?", (codigo,)).fetchone()
        if projeto is None:
            cur = db.execute(
                "INSERT INTO projetos (codigo, cliente_id, ano, pasta) VALUES (?, ?, ?, ?)",
                (codigo, cliente_id, datetime.now(timezone.utc).year, f"{codigo} - {cliente['nome']}"),
            )
            projeto_id = cur.lastrowid
        else:
            projeto_id = projeto["id"]

        # Gera agora só pra validar que os modelos existem e as substituições
        # rodam — o conteúdo é descartado e remontado no download.
        arquivos = [nome for nome, _ in gerar(ctx, dir_modelos)]

        db.execute(
            """UPDATE geracoes_documentos
               SET status = 'pronto', cliente_id = ?, projeto_id = ?, projeto_codigo = ?,
                   contexto = ?, arquivos = ?, erro = NULL,
                   atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (cliente_id, projeto_id, codigo, json.dumps(ctx, ensure_ascii=False), json.dumps(arquivos), geracao_id),
        )
        db.commit()
        logger.info("Geração %s concluída: %s", geracao_id, ", ".join(arquivos))
        return arquivos
    except Exception as e:
        db.rollback()
        logger.exception("Geração %s falhou", geracao_id)
        db.execute(
            """UPDATE geracoes_documentos SET status = 'erro', erro = ?,
               atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?""",
            (str(e)[:500], geracao_id),
        )
        db.commit()
        raise
