from flask import Blueprint, jsonify, request

from app.db import get_db
from app.errors import ApiError
from app.socket import broadcast_mensagem

bp = Blueprint("mensagens_publicas", __name__, url_prefix="/api/v1/publico/indicacoes")

# Sem login: quem clicou no link de indicação do parceiro não tem conta em
# nenhum dos dois apps. O `chat_token` (aleatório, não sequencial) é o único
# jeito de acessar essa conversa — não expor o `id` numérico da indicação aqui.


def _get_or_404(db, chat_token):
    row = db.execute("SELECT * FROM indicacoes WHERE chat_token = ?", (chat_token,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", "Conversa não encontrada", 404)
    return row


@bp.get("/<chat_token>")
def get_indicacao(chat_token):
    db = get_db()
    row = _get_or_404(db, chat_token)
    return jsonify(
        {
            "nome_indicado": row["nome_indicado"],
            "status": row["status"],
            "criado_em": row["criado_em"],
        }
    )


@bp.get("/<chat_token>/mensagens")
def list_mensagens(chat_token):
    db = get_db()
    indicacao = _get_or_404(db, chat_token)
    rows = db.execute(
        "SELECT id, autor_tipo, texto, criado_em FROM mensagens WHERE indicacao_id = ? ORDER BY criado_em, id",
        (indicacao["id"],),
    ).fetchall()
    return jsonify({"data": [dict(r) for r in rows]})


@bp.post("/<chat_token>/mensagens")
def enviar_mensagem(chat_token):
    db = get_db()
    indicacao = _get_or_404(db, chat_token)
    body = request.get_json(force=True, silent=True) or {}
    texto = (body.get("texto") or "").strip()
    if not texto:
        raise ApiError("VALIDATION_ERROR", "Campo 'texto' é obrigatório", 400)

    cur = db.execute(
        "INSERT INTO mensagens (indicacao_id, autor_tipo, texto) VALUES (?, 'cliente', ?)",
        (indicacao["id"], texto),
    )
    db.commit()
    row = db.execute(
        "SELECT id, autor_tipo, texto, criado_em FROM mensagens WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    mensagem = dict(row)
    broadcast_mensagem(indicacao["id"], mensagem)
    return jsonify(mensagem), 201
