import sqlite3

from flask import Blueprint, g, jsonify, request

from app.auth import require_login
from app.db import get_db
from app.errors import ApiError
from app.socket import broadcast_suporte, broadcast_suporte_encerrado

bp = Blueprint("suporte", __name__, url_prefix="/api/v1/suporte")
bp.before_request(require_login)

# Conversas de suporte interno: um operador fala com "suporte" (qualquer admin
# pode ver/responder). Cada conversa (thread) é encerrada por um admin, e só
# então o operador pode avaliar quem o atendeu.


def _get_thread_or_404(db, thread_id):
    row = db.execute("SELECT * FROM suporte_threads WHERE id = ?", (thread_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Conversa {thread_id} não encontrada", 404)
    return row


def _require_own_thread_or_admin(thread):
    if g.user["papel"] != "admin" and thread["usuario_id"] != g.user["id"]:
        raise ApiError("FORBIDDEN", "Essa conversa não é sua", 403)


@bp.get("/threads")
def list_threads():
    """Inbox do admin: uma linha por conversa, mais recente primeiro."""
    if g.user["papel"] != "admin":
        raise ApiError("FORBIDDEN", "Acesso restrito a administradores", 403)
    db = get_db()
    status = request.args.get("status")
    where = "WHERE t.status = ?" if status else ""
    params = [status] if status else []
    rows = db.execute(
        f"""SELECT t.*, u.nome AS usuario_nome,
                   (SELECT texto FROM suporte_mensagens WHERE thread_id = t.id ORDER BY criado_em DESC, id DESC LIMIT 1) AS ultima_mensagem,
                   (SELECT criado_em FROM suporte_mensagens WHERE thread_id = t.id ORDER BY criado_em DESC, id DESC LIMIT 1) AS ultima_mensagem_em
            FROM suporte_threads t JOIN usuarios u ON u.id = t.usuario_id
            {where}
            ORDER BY COALESCE(ultima_mensagem_em, t.criado_em) DESC""",
        params,
    ).fetchall()
    return jsonify({"data": [dict(r) for r in rows]})


@bp.get("/minha-thread")
def minha_thread():
    """A conversa mais recente do operador logado (aberta ou já encerrada, pra
    ele ver o resultado/avaliar), ou null se ele nunca falou com o suporte."""
    if g.user["papel"] == "admin":
        raise ApiError("VALIDATION_ERROR", "Admin não tem conversa própria — use /suporte/threads", 400)
    db = get_db()
    row = db.execute(
        "SELECT * FROM suporte_threads WHERE usuario_id = ? ORDER BY criado_em DESC LIMIT 1", (g.user["id"],)
    ).fetchone()
    return jsonify(dict(row) if row else None)


@bp.get("/threads/<int:thread_id>/avaliacao")
def get_avaliacao(thread_id):
    db = get_db()
    thread = _get_thread_or_404(db, thread_id)
    _require_own_thread_or_admin(thread)
    row = db.execute("SELECT * FROM suporte_avaliacoes WHERE thread_id = ?", (thread_id,)).fetchone()
    if row is None:
        return jsonify(None)
    avaliacao = dict(row)
    avaliacao["positiva"] = bool(avaliacao["positiva"])
    return jsonify(avaliacao)


@bp.get("/threads/<int:thread_id>/mensagens")
def list_mensagens(thread_id):
    db = get_db()
    thread = _get_thread_or_404(db, thread_id)
    _require_own_thread_or_admin(thread)
    rows = db.execute(
        """SELECT m.*, a.nome AS autor_nome, a.papel AS autor_papel
           FROM suporte_mensagens m JOIN usuarios a ON a.id = m.autor_usuario_id
           WHERE m.thread_id = ? ORDER BY m.criado_em, m.id""",
        (thread_id,),
    ).fetchall()
    return jsonify({"data": [dict(r) for r in rows]})


@bp.post("/mensagens")
def enviar_mensagem():
    body = request.get_json(force=True, silent=True) or {}
    texto = (body.get("texto") or "").strip()
    if not texto:
        raise ApiError("VALIDATION_ERROR", "Campo 'texto' é obrigatório", 400)

    db = get_db()

    if g.user["papel"] == "admin":
        thread_id = body.get("thread_id")
        if not thread_id:
            raise ApiError("VALIDATION_ERROR", "Admin precisa informar 'thread_id'", 400)
        thread = _get_thread_or_404(db, thread_id)
        if thread["status"] != "aberto":
            raise ApiError("VALIDATION_ERROR", "Essa conversa já foi encerrada", 400)
    else:
        thread = db.execute(
            "SELECT * FROM suporte_threads WHERE usuario_id = ? ORDER BY criado_em DESC LIMIT 1", (g.user["id"],)
        ).fetchone()
        if thread is None or thread["status"] != "aberto":
            cur = db.execute("INSERT INTO suporte_threads (usuario_id) VALUES (?)", (g.user["id"],))
            db.commit()
            thread = db.execute("SELECT * FROM suporte_threads WHERE id = ?", (cur.lastrowid,)).fetchone()

    cur = db.execute(
        "INSERT INTO suporte_mensagens (thread_id, autor_usuario_id, texto) VALUES (?, ?, ?)",
        (thread["id"], g.user["id"], texto),
    )
    db.commit()
    row = db.execute(
        """SELECT m.*, a.nome AS autor_nome, a.papel AS autor_papel
           FROM suporte_mensagens m JOIN usuarios a ON a.id = m.autor_usuario_id
           WHERE m.id = ?""",
        (cur.lastrowid,),
    ).fetchone()
    mensagem = dict(row)
    broadcast_suporte(thread["id"], thread["usuario_id"], mensagem)
    return jsonify(mensagem), 201


@bp.post("/threads/<int:thread_id>/encerrar")
def encerrar_thread(thread_id):
    if g.user["papel"] != "admin":
        raise ApiError("FORBIDDEN", "Acesso restrito a administradores", 403)
    db = get_db()
    thread = _get_thread_or_404(db, thread_id)
    if thread["status"] != "aberto":
        raise ApiError("VALIDATION_ERROR", "Essa conversa já está encerrada", 400)

    db.execute(
        """UPDATE suporte_threads
           SET status = 'encerrado', admin_usuario_id = ?, encerrado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now')
           WHERE id = ?""",
        (g.user["id"], thread_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM suporte_threads WHERE id = ?", (thread_id,)).fetchone()
    thread = dict(row)
    broadcast_suporte_encerrado(thread["usuario_id"], thread)
    return jsonify(thread)


@bp.post("/threads/<int:thread_id>/avaliacao")
def avaliar_thread(thread_id):
    db = get_db()
    thread = _get_thread_or_404(db, thread_id)
    if g.user["papel"] == "admin" or thread["usuario_id"] != g.user["id"]:
        raise ApiError("FORBIDDEN", "Só quem abriu a conversa pode avaliar", 403)
    if thread["status"] != "encerrado":
        raise ApiError("VALIDATION_ERROR", "Só é possível avaliar uma conversa já encerrada", 400)

    body = request.get_json(force=True, silent=True) or {}
    if not isinstance(body.get("positiva"), bool):
        raise ApiError("VALIDATION_ERROR", "Campo 'positiva' (true/false) é obrigatório", 400)

    try:
        db.execute(
            "INSERT INTO suporte_avaliacoes (thread_id, admin_usuario_id, positiva, comentario) VALUES (?, ?, ?, ?)",
            (thread_id, thread["admin_usuario_id"], int(body["positiva"]), (body.get("comentario") or "").strip() or None),
        )
    except sqlite3.IntegrityError:
        raise ApiError("CONFLICT", "Essa conversa já foi avaliada", 409)
    db.commit()
    row = db.execute("SELECT * FROM suporte_avaliacoes WHERE thread_id = ?", (thread_id,)).fetchone()
    avaliacao = dict(row)
    avaliacao["positiva"] = bool(avaliacao["positiva"])
    return jsonify(avaliacao), 201
