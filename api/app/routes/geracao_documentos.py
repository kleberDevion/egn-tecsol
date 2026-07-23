import io
import json
import logging
import zipfile

from flask import Blueprint, current_app, g, jsonify, request, send_file

from app.auth import require_login
from app.db import get_db
from app.errors import ApiError
from app.documentos_gerador import GeracaoError, gerar
from app.geracao_documentos import listar_pendentes
from app.solarz import SolarzApiError

bp = Blueprint("geracao_documentos", __name__, url_prefix="/api/v1/geracao-documentos")
bp.before_request(require_login)

logger = logging.getLogger(__name__)


def _para_dict(row):
    d = dict(row)
    d["arquivos"] = json.loads(d["arquivos"]) if d.get("arquivos") else []
    return d


@bp.get("/pendentes")
def pendentes():
    """Negócios no estágio "Gerar Documentação" da Solarz — os cards da tela.
    Marca quais já foram gerados aqui, pra não gerar duas vezes sem querer."""
    db = get_db()
    try:
        deals = listar_pendentes()
    except SolarzApiError as e:
        logger.error("Falha ao listar pendentes na Solarz: %s", e)
        raise ApiError("UPSTREAM_ERROR", "Não foi possível consultar o CRM agora.", 502)

    ja_gerados = {
        r["solarz_deal_id"]
        for r in db.execute("SELECT DISTINCT solarz_deal_id FROM geracoes_documentos WHERE status = 'pronto'")
    }

    return jsonify(
        {
            "data": [
                {
                    "solarz_deal_id": d["id"],
                    "nome_negocio": d.get("name"),
                    "valor_projeto": d.get("value"),
                    "criado_em": d.get("createdAt"),
                    "ja_gerado": d["id"] in ja_gerados,
                }
                for d in deals
            ]
        }
    )


@bp.get("/proximo-pedido")
def proximo_pedido():
    """Sugestão pro campo "número do pedido": sequencial 01, 02, 03..."""
    db = get_db()
    row = db.execute(
        "SELECT numero_pedido FROM geracoes_documentos WHERE numero_pedido ~ '^[0-9]+$' "
        "ORDER BY CAST(numero_pedido AS INTEGER) DESC LIMIT 1"
    ).fetchone()
    proximo = (int(row["numero_pedido"]) + 1) if row else 1
    return jsonify({"numero_pedido": f"{proximo:02d}"})


@bp.get("")
def listar():
    db = get_db()
    rows = db.execute(
        """SELECT g.*, c.nome AS cliente_nome
             FROM geracoes_documentos g
             LEFT JOIN clientes c ON c.id = g.cliente_id
            ORDER BY g.criado_em DESC LIMIT 100"""
    ).fetchall()
    return jsonify({"data": [_para_dict(r) for r in rows]})


@bp.get("/<int:geracao_id>")
def detalhe(geracao_id):
    db = get_db()
    row = db.execute("SELECT * FROM geracoes_documentos WHERE id = ?", (geracao_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Geração {geracao_id} não encontrada", 404)
    return jsonify(_para_dict(row))


@bp.post("")
def criar():
    """Um clique gera tudo. O operador só informa CFT e número do pedido —
    o resto é buscado na Solarz pelo próprio servidor."""
    body = request.get_json(force=True, silent=True) or {}
    deal_id = body.get("solarz_deal_id")
    numero_cft = (body.get("numero_cft") or "").strip()
    numero_pedido = (body.get("numero_pedido") or "").strip()

    if not deal_id:
        raise ApiError("VALIDATION_ERROR", "Campo 'solarz_deal_id' é obrigatório", 400)
    if not numero_cft:
        raise ApiError("VALIDATION_ERROR", "Informe o CFT (gerado pelo engenheiro no site do governo)", 400)
    if not numero_pedido:
        raise ApiError("VALIDATION_ERROR", "Informe o número do pedido", 400)

    db = get_db()
    cur = db.execute(
        """INSERT INTO geracoes_documentos (solarz_deal_id, numero_pedido, numero_cft, solicitado_por)
           VALUES (?, ?, ?, ?)""",
        (deal_id, numero_pedido, numero_cft, g.user["id"]),
    )
    db.commit()
    geracao_id = cur.lastrowid

    # Enfileira no worker; sem broker (dev), roda na hora pra não travar o fluxo.
    try:
        from app.tasks import gerar_documentos

        gerar_documentos.send(geracao_id)
    except Exception as e:
        logger.warning("Broker indisponível (%s) — gerando documentos inline.", e)
        from app.geracao_documentos import executar

        try:
            executar(db, geracao_id, current_app.config["MODELOS_DIR"])
        except Exception:
            pass  # o status de erro já foi gravado por executar()

    row = db.execute("SELECT * FROM geracoes_documentos WHERE id = ?", (geracao_id,)).fetchone()
    return jsonify(_para_dict(row)), 202


def _documentos_da_geracao(geracao_id):
    """Remonta os .docx a partir do contexto salvo. Nada vem de disco, então
    funciona igual em qualquer servidor e não depende de deploy anterior."""
    db = get_db()
    row = db.execute("SELECT * FROM geracoes_documentos WHERE id = ?", (geracao_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", "Geração não encontrada", 404)
    if not row["contexto"]:
        raise ApiError("NOT_FOUND", "Essa geração não tem dados guardados. Gere novamente.", 404)

    contexto = json.loads(row["contexto"])
    try:
        arquivos = gerar(contexto, current_app.config["MODELOS_DIR"])
    except GeracaoError as e:
        raise ApiError("CONFIG_ERROR", str(e), 503)
    return row, arquivos


@bp.get("/<int:geracao_id>/arquivos/<path:nome>")
def baixar(geracao_id, nome):
    _, arquivos = _documentos_da_geracao(geracao_id)
    for arquivo, conteudo in arquivos:
        if arquivo == nome:
            return send_file(
                io.BytesIO(conteudo),
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                as_attachment=True,
                download_name=nome,
            )
    raise ApiError("NOT_FOUND", "Arquivo não encontrado", 404)


@bp.get("/<int:geracao_id>/download")
def baixar_tudo(geracao_id):
    """Todos os documentos num .zip só — o operador baixa de uma vez e anexa
    na Solarz."""
    row, arquivos = _documentos_da_geracao(geracao_id)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, conteudo in arquivos:
            zf.writestr(nome, conteudo)
    buffer.seek(0)

    codigo = row["projeto_codigo"] or f"negocio-{row['solarz_deal_id']}"
    return send_file(buffer, mimetype="application/zip", as_attachment=True, download_name=f"{codigo}.zip")
