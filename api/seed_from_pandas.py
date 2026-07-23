"""
Script de carga (seed) do banco tecsol.db a partir dos dados reais encontrados em:
  - 2026/2026/PJ-*  (pastas de projeto -> clientes, projetos, documentos)
  - DAVI/DAVI/Não Alterar/template_import_....xlsx (abas Usinas, Geração, Metadados)

Uso:
    python seed_from_pandas.py

Deliberadamente NÃO lê as abas "Portais" e "Login concessionária" do arquivo
"Dados - Monitoramento...xlsx", pois contêm usuário/senha em texto puro.
"""

import re
import os

import psycopg

from app.db import Connection
from pathlib import Path

import pandas as pd

API_DIR = Path(__file__).resolve().parent
DATA_ROOT = API_DIR.parent
SCHEMA_PATH = API_DIR / "schema.sql"

PROJETOS_DIR = DATA_ROOT / "2026" / "2026"
TEMPLATE_XLSX = (
    DATA_ROOT / "DAVI" / "DAVI" / "Não Alterar"
    / "template_import_Tecsol Engenharia e Solucoes Energeticas (version 1).xlsx"
)

ANO_REFERENCIA_GERACAO = 2026  # a aba "Geração" não indica o ano explicitamente

BUSINESS_SUBSTRINGS = [
    "LTDA", "MADEIREIRA", "BEACH", "EIRELI", "COMERCIO", "COMÉRCIO",
    "INDUSTRIA", "INDÚSTRIA", "ASSOCIACAO", "ASSOCIAÇÃO", "CONDOMINIO",
    "CONDOMÍNIO", "EMPRESA",
]
BUSINESS_TOKENS = {"ME", "SA", "S/A"}

MESES = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
    "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12,
}


def reset_schema(conn):
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    for tabela in ["geracao", "documentos", "usinas", "projetos", "clientes", "concessionarias"]:
        # TRUNCATE ... RESTART IDENTITY zera a sequence do SERIAL junto (no
        # SQLite isso era feito apagando a linha em sqlite_sequence).
        conn.execute(f"TRUNCATE {tabela} RESTART IDENTITY CASCADE")
    conn.commit()


def infer_tipo(nome):
    upper = nome.upper()
    if any(s in upper for s in BUSINESS_SUBSTRINGS):
        return "PJ"
    tokens = set(re.split(r"\s+", upper))
    if tokens & BUSINESS_TOKENS:
        return "PJ"
    return "PF"


def parse_pasta_projeto(pasta: Path):
    codigo, _, nome_cliente = pasta.name.partition(" - ")
    codigo = codigo.strip()
    nome_cliente = nome_cliente.strip()
    match = re.search(r"PJ-(\d{4})-", codigo)
    ano = int(match.group(1)) if match else None
    return codigo, nome_cliente, ano


def seed_clientes_projetos_documentos(conn):
    pastas_projeto = sorted(p for p in PROJETOS_DIR.iterdir() if p.is_dir() and p.name.startswith("PJ-"))

    clientes_por_nome = {}
    projetos_info = []
    for pasta in pastas_projeto:
        codigo, nome_cliente, ano = parse_pasta_projeto(pasta)
        if not codigo or not nome_cliente or ano is None:
            print(f"  [aviso] pasta ignorada (nome inesperado): {pasta.name}")
            continue
        chave = nome_cliente.lower()
        clientes_por_nome.setdefault(chave, nome_cliente)
        projetos_info.append((codigo, nome_cliente, ano, pasta))

    clientes_df = pd.DataFrame(
        [{"tipo": infer_tipo(nome), "nome": nome} for nome in clientes_por_nome.values()]
    )
    clientes_df.to_sql("clientes", conn, if_exists="append", index=False)
    print(f"  clientes inseridos: {len(clientes_df)}")

    cliente_id_by_nome = {
        nome.lower(): cid
        for cid, nome in conn.execute("SELECT id, nome FROM clientes").fetchall()
    }

    projetos_rows = []
    for codigo, nome_cliente, ano, pasta in projetos_info:
        cliente_id = cliente_id_by_nome[nome_cliente.lower()]
        pasta_relativa = str(pasta.relative_to(DATA_ROOT)).replace("\\", "/")
        projetos_rows.append(
            {"codigo": codigo, "cliente_id": cliente_id, "ano": ano, "pasta": pasta_relativa}
        )
    projetos_df = pd.DataFrame(projetos_rows)
    projetos_df.to_sql("projetos", conn, if_exists="append", index=False)
    print(f"  projetos inseridos: {len(projetos_df)}")

    projeto_id_by_codigo = {
        codigo: pid for pid, codigo in conn.execute("SELECT id, codigo FROM projetos").fetchall()
    }

    documentos_rows = []
    for codigo, _, _, pasta in projetos_info:
        projeto_id = projeto_id_by_codigo[codigo]
        for arquivo in pasta.rglob("*"):
            if not arquivo.is_file():
                continue
            partes_relativas = arquivo.relative_to(pasta).parts
            categoria = partes_relativas[0] if len(partes_relativas) > 1 else "0_Outros"
            extensao = arquivo.suffix[1:].lower() if arquivo.suffix else None
            caminho_relativo = str(arquivo.relative_to(DATA_ROOT)).replace("\\", "/")
            documentos_rows.append(
                {
                    "projeto_id": projeto_id,
                    "categoria": categoria,
                    "nome_arquivo": arquivo.name,
                    "extensao": extensao,
                    "tamanho_bytes": arquivo.stat().st_size,
                    "caminho_relativo": caminho_relativo,
                }
            )
    documentos_df = pd.DataFrame(documentos_rows)
    documentos_df.to_sql("documentos", conn, if_exists="append", index=False)
    print(f"  documentos inseridos: {len(documentos_df)}")


def seed_usinas_e_geracao(conn):
    usinas_df = pd.read_excel(TEMPLATE_XLSX, sheet_name="Usinas", header=1)
    usinas_df = usinas_df[usinas_df["Nome"].notna()].copy()

    col_data = "Data de Instalação (dd/mm/aaaa)"
    usinas_df[col_data] = pd.to_datetime(usinas_df[col_data], errors="coerce").dt.strftime("%Y-%m-%d")

    usinas_out = pd.DataFrame(
        {
            "nome": usinas_df["Nome"].astype(str).str.strip(),
            "cliente_id": None,
            "potencia_kwp": usinas_df["Potência (kWp)"],
            "data_instalacao": usinas_df[col_data],
            "total_investido": usinas_df["Total Investido (R$)"],
            "geracao_anual_esperada": usinas_df[
                "Geração anual esperada (Só é considerado se a geração mensal na aba geração não estiver preenchida)"
            ],
            "cep": usinas_df["CEP"],
            "latitude": usinas_df["Latitude (opcional)"],
            "longitude": usinas_df["Longitude (opcional)"],
        }
    )
    usinas_out = usinas_out.drop_duplicates(subset=["nome"], keep="first")
    usinas_out.to_sql("usinas", conn, if_exists="append", index=False)
    print(f"  usinas inseridas: {len(usinas_out)} (cliente_id não identificado na planilha de origem)")

    usina_id_by_nome = {
        nome: uid for uid, nome in conn.execute("SELECT id, nome FROM usinas").fetchall()
    }

    geracao_df = pd.read_excel(TEMPLATE_XLSX, sheet_name="Geração", header=1)
    geracao_df = geracao_df[geracao_df["Usinas"].notna()].copy()
    geracao_df["nome_usina"] = geracao_df["Usinas"].astype(str).str.split(" || ", regex=False).str[0].str.strip()

    meses_presentes = [m for m in MESES if m in geracao_df.columns]
    longa = geracao_df.melt(
        id_vars=["nome_usina"], value_vars=meses_presentes, var_name="mes_nome", value_name="valor_kwh"
    )
    longa = longa[longa["valor_kwh"].notna()]
    longa["mes"] = longa["mes_nome"].map(MESES)
    longa["usina_id"] = longa["nome_usina"].map(usina_id_by_nome)

    nao_encontradas = longa[longa["usina_id"].isna()]["nome_usina"].unique()
    if len(nao_encontradas):
        print(f"  [aviso] {len(nao_encontradas)} usina(s) da aba Geração sem correspondência em Usinas, ignoradas")

    longa = longa[longa["usina_id"].notna()].copy()
    longa["usina_id"] = longa["usina_id"].astype(int)
    longa["ano"] = ANO_REFERENCIA_GERACAO
    longa = longa.drop_duplicates(subset=["usina_id", "ano", "mes"], keep="first")

    geracao_out = longa[["usina_id", "ano", "mes", "valor_kwh"]]
    geracao_out.to_sql("geracao", conn, if_exists="append", index=False)
    print(f"  registros de geração inseridos: {len(geracao_out)} (ano assumido: {ANO_REFERENCIA_GERACAO})")


def seed_concessionarias(conn):
    metadados_df = pd.read_excel(TEMPLATE_XLSX, sheet_name="Metadados", header=1)
    coluna = "Concessionárias"
    valores = metadados_df[coluna].dropna()
    valores = valores[valores.str.contains(r"\|\|\s*id:", regex=True, na=False)]
    nomes = sorted({v.split(" || ")[0].strip() for v in valores})

    concessionarias_out = pd.DataFrame({"nome": nomes})
    concessionarias_out.to_sql("concessionarias", conn, if_exists="append", index=False)
    print(f"  concessionárias inseridas: {len(concessionarias_out)}")


def main():
    print(f"Banco de destino: {os.environ['DATABASE_URL']}")
    conn = Connection(psycopg.connect(os.environ["DATABASE_URL"]))
    try:
        print("Recriando schema...")
        reset_schema(conn)

        print("Carregando clientes / projetos / documentos das pastas 2026/...")
        seed_clientes_projetos_documentos(conn)

        print("Carregando usinas e geração da planilha DAVI...")
        seed_usinas_e_geracao(conn)

        print("Carregando concessionárias da planilha DAVI...")
        seed_concessionarias(conn)

        conn.commit()
        print("Seed concluído com sucesso.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
