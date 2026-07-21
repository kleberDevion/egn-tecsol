import logging
import random
import re
import sqlite3

from flask import Blueprint, g, jsonify, request, session

from app.auth import hash_password, require_admin, verify_password
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query
from app.solarz import PIPELINE_PRE_VENDAS, STAGE_PRE_VENDAS_PROSPECT, SolarzApiError, criar_negocio

logger = logging.getLogger(__name__)

bp = Blueprint("indicadores", __name__, url_prefix="/api/v1/indicadores")


def _public_indicador(row, db=None):
    total_cliques = 0
    if db is not None:
        total_cliques = db.execute(
            "SELECT COUNT(*) FROM indicador_cliques WHERE indicador_id = ?", (row["id"],)
        ).fetchone()[0]
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "telefone": row["telefone"],
        "codigo_indicacao": row["codigo_indicacao"],
        "recrutado_por_id": row["recrutado_por_id"],
        "nivel": row["nivel"],
        "total_vendas": row["total_vendas"],
        "total_ganhos": row["total_ganhos"],
        "total_cliques": total_cliques,
        "criado_em": row["criado_em"],
        "ultimo_login_em": row["ultimo_login_em"],
    }


def get_current_indicador():
    if "indicador" in g:
        return g.indicador

    indicador_id = session.get("indicador_id")
    if indicador_id is None:
        g.indicador = None
        return None

    db = get_db()
    row = db.execute("SELECT * FROM indicadores WHERE id = ? AND ativo = 1", (indicador_id,)).fetchone()
    g.indicador = dict(row) if row is not None else None
    return g.indicador


def require_indicador_login():
    if get_current_indicador() is None:
        raise ApiError("UNAUTHORIZED", "Login necessário", 401)


def _gerar_codigo(db, nome):
    prefixo = re.sub(r"[^A-Za-z]", "", nome[:4]).upper()
    if len(prefixo) < 2:
        prefixo = "USER"
    for _ in range(20):
        codigo = f"TECSOL-{prefixo}{random.randint(0, 999):03d}"
        existe = db.execute("SELECT 1 FROM indicadores WHERE codigo_indicacao = ?", (codigo,)).fetchone()
        if existe is None:
            return codigo
    raise ApiError("CONFLICT", "Não foi possível gerar um código de indicação único", 409)


@bp.get("")
def list_indicadores():
    """Listagem para o CRM (admin) gerenciar os parceiros cadastrados."""
    require_admin()
    db = get_db()
    rows, pagination = paginate_query(
        db,
        "SELECT * FROM indicadores ORDER BY criado_em DESC",
        "SELECT COUNT(*) FROM indicadores",
        [],
    )
    return jsonify({"data": [_public_indicador(r) for r in rows], "pagination": pagination})


@bp.post("/auth/signup")
def signup():
    body = request.get_json(force=True, silent=True) or {}
    nome, email, senha = body.get("nome"), body.get("email"), body.get("senha")
    telefone = body.get("telefone")
    if not nome:
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)
    if not email:
        raise ApiError("VALIDATION_ERROR", "Campo 'email' é obrigatório", 400)
    if not senha or len(senha) < 8:
        raise ApiError("VALIDATION_ERROR", "Senha deve ter ao menos 8 caracteres", 400)

    # Convite: o mesmo codigo_indicacao que já serve pro link de cliente
    # (/i/{codigo}) também recruta novos indicadores, via /auth?convite={codigo}.
    # Código inválido/inexistente não bloqueia o cadastro — só não vincula a
    # ninguém, pra um link expirado/errado não impedir a pessoa de criar conta.
    recrutado_por_id = None
    codigo_convite = body.get("codigo_convite")
    if codigo_convite:
        recrutador = get_db().execute(
            "SELECT id FROM indicadores WHERE codigo_indicacao = ? AND ativo = 1", (codigo_convite,)
        ).fetchone()
        if recrutador is not None:
            recrutado_por_id = recrutador["id"]

    db = get_db()
    codigo = _gerar_codigo(db, nome)
    try:
        cur = db.execute(
            """INSERT INTO indicadores (nome, email, telefone, senha_hash, codigo_indicacao, recrutado_por_id, ultimo_login_em)
               VALUES (?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ','now'))""",
            (nome, email, telefone, hash_password(senha), codigo, recrutado_por_id),
        )
    except sqlite3.IntegrityError:
        raise ApiError("CONFLICT", f"Já existe uma conta com o e-mail '{email}'", 409)
    db.commit()
    session["indicador_id"] = cur.lastrowid
    row = db.execute("SELECT * FROM indicadores WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_public_indicador(row, db)), 201


@bp.post("/auth/login")
def login():
    body = request.get_json(force=True, silent=True) or {}
    email, senha = body.get("email"), body.get("senha")
    if not email or not senha:
        raise ApiError("VALIDATION_ERROR", "Informe e-mail e senha", 400)

    db = get_db()
    row = db.execute("SELECT * FROM indicadores WHERE email = ? AND ativo = 1", (email,)).fetchone()
    if row is None or not verify_password(senha, row["senha_hash"]):
        raise ApiError("UNAUTHORIZED", "E-mail ou senha inválidos", 401)

    session["indicador_id"] = row["id"]
    db.execute(
        "UPDATE indicadores SET ultimo_login_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
        (row["id"],),
    )
    db.commit()
    row = db.execute("SELECT * FROM indicadores WHERE id = ?", (row["id"],)).fetchone()
    return jsonify(_public_indicador(row, db))


@bp.post("/auth/logout")
def logout():
    require_indicador_login()
    session.pop("indicador_id", None)
    return "", 204


@bp.get("/me")
def me():
    require_indicador_login()
    return jsonify(_public_indicador(g.indicador, get_db()))


@bp.patch("/me")
def update_me():
    require_indicador_login()
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in ("nome", "telefone")}
    if "nome" in updates and not updates["nome"]:
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' não pode ficar vazio", 400)

    if updates:
        db = get_db()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), g.indicador["id"]]
        db.execute(
            f"UPDATE indicadores SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )
        db.commit()

    db = get_db()
    row = db.execute("SELECT * FROM indicadores WHERE id = ?", (g.indicador["id"],)).fetchone()
    return jsonify(_public_indicador(row, db))


@bp.post("/sync")
def sync_minhas_indicacoes():
    """Botão "Atualizar" do app: sincroniza na hora (inline) só as indicações
    do indicador logado, pra ele não precisar esperar o ciclo do Celery beat."""
    require_indicador_login()
    from app.sync_indicacoes import sincronizar

    try:
        atualizadas = sincronizar(get_db(), indicador_id=g.indicador["id"])
    except Exception:
        logger.exception("Sync sob demanda falhou (indicador %s)", g.indicador["id"])
        raise ApiError("UPSTREAM_ERROR", "Não foi possível consultar o CRM agora. Tente de novo em instantes.", 502)
    return jsonify({"atualizadas": atualizadas})


@bp.get("/minhas-indicacoes")
def minhas_indicacoes():
    require_indicador_login()
    db = get_db()
    rows, pagination = paginate_query(
        db,
        "SELECT * FROM indicacoes WHERE indicador_id = ? ORDER BY criado_em DESC",
        "SELECT COUNT(*) FROM indicacoes WHERE indicador_id = ?",
        [g.indicador["id"]],
    )
    return jsonify({"data": [dict(r) for r in rows], "pagination": pagination})


STATUS_AUTOATUALIZAVEIS = ("recebido", "em_atendimento", "negociacao", "perdido", "cancelado")


@bp.patch("/indicacoes/<int:indicacao_id>")
def atualizar_minha_indicacao(indicacao_id):
    """O indicador pode acompanhar/atualizar o status da própria indicação
    (como faz o contato, se está negociando etc.), mas nunca 'fechado' — essa
    transição envolve valor_sistema/comissao_gerada e só a Tecsol confirma,
    via PATCH /api/v1/indicacoes/{id} (autenticado como usuário do CRM)."""
    require_indicador_login()
    db = get_db()
    row = db.execute(
        "SELECT * FROM indicacoes WHERE id = ? AND indicador_id = ?", (indicacao_id, g.indicador["id"])
    ).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Indicação {indicacao_id} não encontrada", 404)

    body = request.get_json(force=True, silent=True) or {}
    status = body.get("status")
    if status not in STATUS_AUTOATUALIZAVEIS:
        raise ApiError(
            "VALIDATION_ERROR",
            f"'status' deve ser um de {STATUS_AUTOATUALIZAVEIS}. Fechar uma venda é confirmado pela Tecsol.",
            400,
        )

    db.execute(
        "UPDATE indicacoes SET status = ?, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
        (status, indicacao_id),
    )
    db.commit()
    updated = db.execute("SELECT * FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone()
    return jsonify(dict(updated))


@bp.post("/indicacoes")
def criar_indicacao():
    require_indicador_login()
    body = request.get_json(force=True, silent=True) or {}
    nome_indicado = body.get("nome_indicado")
    telefone_indicado = body.get("telefone_indicado")
    if not nome_indicado:
        raise ApiError("VALIDATION_ERROR", "Campo 'nome_indicado' é obrigatório", 400)
    if not telefone_indicado:
        raise ApiError("VALIDATION_ERROR", "Campo 'telefone_indicado' é obrigatório", 400)

    nivel_interesse = body.get("nivel_interesse", "nao_sei")
    if nivel_interesse not in ("sim", "talvez", "nao_sei"):
        raise ApiError("VALIDATION_ERROR", "nivel_interesse inválido", 400)

    # valor_sistema/comissao_gerada nunca vêm do corpo da requisição: só a Tecsol
    # (via api/app/routes/indicacoes.py, autenticado como operador/admin) define
    # esses valores ao encerrar o atendimento.
    db = get_db()
    cur = db.execute(
        """INSERT INTO indicacoes
           (indicador_id, nome_indicado, telefone_indicado, cidade, conta_energia_estimada, nivel_interesse, observacoes, chat_token)
           VALUES (?, ?, ?, ?, ?, ?, ?, lower(hex(randomblob(16))))""",
        (
            g.indicador["id"],
            nome_indicado,
            telefone_indicado,
            body.get("cidade"),
            body.get("conta_energia_estimada"),
            nivel_interesse,
            body.get("observacoes"),
        ),
    )
    db.commit()
    indicacao_id = cur.lastrowid

    # Mesma lógica do form público (app/routes/indicacoes_publicas.py): a Solarz
    # é o CRM real, mas uma falha ao chamar ela não pode derrubar o cadastro local.
    try:
        deal_id = criar_negocio(
            nome_negocio=f"Indicação (app) - {nome_indicado}",
            pipeline_id=PIPELINE_PRE_VENDAS,
            pipeline_stage_id=STAGE_PRE_VENDAS_PROSPECT,
            pessoa_nome=nome_indicado,
            pessoa_telefone=telefone_indicado,
        )
        db.execute("UPDATE indicacoes SET solarz_deal_id = ? WHERE id = ?", (deal_id, indicacao_id))
        db.commit()
    except SolarzApiError as e:
        logger.error("Falha ao criar negócio na Solarz para indicacao %s: %s", indicacao_id, e)

    row = db.execute("SELECT * FROM indicacoes WHERE id = ?", (indicacao_id,)).fetchone()
    return jsonify(dict(row)), 201
