"""
Importa o histórico completo de projetos homologados (2016-2026) a partir de:
  - 06-HOMOLOGADOS/06-HOMOLOGADOS/<ano>/PJ-* (pastas de projeto -> clientes, projetos)

Só cria registros de clientes/projetos (não migra os documentos/arquivos).
Idempotente: pula qualquer código de projeto que já exista no banco, então pode
ser rodado de novo com segurança (ex.: depois de adicionar mais pastas).

Uso:
    python seed_homologados.py           # aplica de verdade
    python seed_homologados.py --dry-run # só mostra o que seria feito
"""

import re
import os

import psycopg

from app.db import Connection
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent
DATA_ROOT = API_DIR.parent
SCHEMA_PATH = API_DIR / "schema.sql"

SOURCE_DIR = DATA_ROOT / "06-HOMOLOGADOS" / "06-HOMOLOGADOS"

BUSINESS_SUBSTRINGS = [
    "LTDA", "MADEIREIRA", "BEACH", "EIRELI", "COMERCIO", "COMÉRCIO",
    "INDUSTRIA", "INDÚSTRIA", "ASSOCIACAO", "ASSOCIAÇÃO", "CONDOMINIO",
    "CONDOMÍNIO", "EMPRESA", "IGREJA", "PANIFICADORA", "PANADARIA",
    "ACADEMIA", "DISTRIBUIDORA", "EMBALAGENS", "CONTABILIDADE", "IMOVEIS",
    "IMÓVEIS", "SEGURANCA", "SEGURANÇA", "PARK", "HOLDING",
]
BUSINESS_TOKENS = {"ME", "SA", "S/A"}


def infer_tipo(nome):
    upper = nome.upper()
    if any(s in upper for s in BUSINESS_SUBSTRINGS):
        return "PJ"
    tokens = set(re.split(r"\s+", upper))
    if tokens & BUSINESS_TOKENS:
        return "PJ"
    return "PF"


def infer_status(nome_cliente):
    upper = nome_cliente.upper()
    if "CANCELADO" in upper or "CANCELADA" in upper:
        return "cancelado"
    if "DESISTENTE" in upper:
        return "desistente"
    return "ativo"


def parse_pasta_projeto(pasta: Path, ano_pasta: int):
    codigo, _, nome_cliente = pasta.name.partition(" - ")
    codigo = codigo.strip()
    nome_cliente = nome_cliente.strip() or codigo
    match = re.search(r"PJ-(\d{4})", codigo)
    ano = int(match.group(1)) if match else ano_pasta
    return codigo, nome_cliente, ano


def coletar_pastas():
    pastas = []
    for ano_dir in sorted(SOURCE_DIR.iterdir()):
        if not ano_dir.is_dir():
            continue
        try:
            ano_pasta = int(ano_dir.name)
        except ValueError:
            continue
        for p in sorted(ano_dir.iterdir()):
            if p.is_dir() and p.name.startswith("PJ-"):
                pastas.append((ano_pasta, p))
    return pastas


def montar_projetos_info():
    pastas = coletar_pastas()
    codigos_vistos = {}
    projetos_info = []
    for ano_pasta, pasta in pastas:
        codigo, nome_cliente, ano = parse_pasta_projeto(pasta, ano_pasta)
        if codigo in codigos_vistos:
            sufixo = codigos_vistos[codigo] + 1
            codigos_vistos[codigo] = sufixo
            codigo_original = codigo
            codigo = f"{codigo}-DUP{sufixo}"
            print(f"  [aviso] código duplicado '{codigo_original}' (pasta: {pasta.name}) -> renomeado para '{codigo}'")
        else:
            codigos_vistos[codigo] = 1
        status = infer_status(nome_cliente)
        pasta_relativa = str(pasta.relative_to(DATA_ROOT)).replace("\\", "/")
        projetos_info.append(
            {
                "codigo": codigo,
                "nome_cliente": nome_cliente,
                "ano": ano,
                "pasta": pasta_relativa,
                "status": status,
            }
        )
    return projetos_info


def main():
    dry_run = "--dry-run" in sys.argv

    if not SOURCE_DIR.exists():
        print(f"Pasta de origem não encontrada: {SOURCE_DIR}")
        sys.exit(1)

    print(f"Lendo pastas de projeto em: {SOURCE_DIR}")
    projetos_info = montar_projetos_info()
    print(f"Pastas de projeto encontradas: {len(projetos_info)}")

    conn = Connection(psycopg.connect(os.environ["DATABASE_URL"]))
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    codigos_existentes = {row[0] for row in conn.execute("SELECT codigo FROM projetos")}
    novos = [p for p in projetos_info if p["codigo"] not in codigos_existentes]
    ja_existiam = len(projetos_info) - len(novos)
    print(f"Já existentes no banco (pulados): {ja_existiam}")
    print(f"Novos a importar: {len(novos)}")

    por_status = {}
    for p in novos:
        por_status[p["status"]] = por_status.get(p["status"], 0) + 1
    print(f"Novos por status: {por_status}")

    if dry_run:
        print("\n--dry-run: nenhuma alteração foi salva. Amostra dos primeiros 10 novos registros:")
        for p in novos[:10]:
            print(f"  {p['codigo']:<28} {p['ano']}  {p['status']:<11} {p['nome_cliente']}")
        conn.close()
        return

    clientes_existentes = {
        nome.lower(): cid for cid, nome in conn.execute("SELECT id, nome FROM clientes").fetchall()
    }

    clientes_inseridos = 0
    for p in novos:
        chave = p["nome_cliente"].lower()
        if chave in clientes_existentes:
            continue
        cur = conn.execute(
            "INSERT INTO clientes (tipo, nome) VALUES (?, ?)",
            (infer_tipo(p["nome_cliente"]), p["nome_cliente"]),
        )
        clientes_existentes[chave] = cur.lastrowid
        clientes_inseridos += 1

    for p in novos:
        cliente_id = clientes_existentes[p["nome_cliente"].lower()]
        conn.execute(
            "INSERT INTO projetos (codigo, cliente_id, ano, pasta, status) VALUES (?, ?, ?, ?, ?)",
            (p["codigo"], cliente_id, p["ano"], p["pasta"], p["status"]),
        )

    conn.commit()
    conn.close()
    print(f"\nClientes novos inseridos: {clientes_inseridos}")
    print(f"Projetos novos inseridos: {len(novos)}")
    print("Importação concluída com sucesso.")


if __name__ == "__main__":
    main()
