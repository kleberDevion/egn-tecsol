import os

from flask import request, session
from flask_socketio import SocketIO, emit, join_room

from app import presence
from app.db import get_db


def _origens_do_socket():
    """Mesma lista branca do CORS das rotas REST (CORS_ORIGINS). Não dá pra
    usar "*" aqui: o cliente conecta com credenciais (o cookie de sessão), e o
    navegador recusa `Access-Control-Allow-Origin: *` nesse caso. Sem a
    variável definida (dev), libera geral."""
    valor = os.environ.get("CORS_ORIGINS", "").strip()
    origens = [o.strip().rstrip("/") for o in valor.split(",") if o.strip()]
    return origens or "*"


socketio = SocketIO(manage_session=True, cors_allowed_origins=_origens_do_socket(), cors_credentials=True)


def _current_user_row():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    db = get_db()
    return db.execute("SELECT * FROM usuarios WHERE id = ? AND ativo = 1", (user_id,)).fetchone()


def _broadcast_presence():
    emit("presence:update", {"online_user_ids": list(presence.get_online_user_ids())}, room="admins")


def _indicacao_room(indicacao_id):
    return f"indicacao:{indicacao_id}"


def _suporte_room(thread_usuario_id):
    return f"suporte:{thread_usuario_id}"


def broadcast_mensagem(indicacao_id, mensagem):
    """Chamado pelas rotas REST (não pelo socket) após INSERT em `mensagens`,
    pra empurrar a mensagem em tempo real pra quem está com a sala aberta."""
    socketio.emit("mensagem:nova", mensagem, room=_indicacao_room(indicacao_id))


def broadcast_suporte(thread_id, usuario_id, mensagem):
    """Empurra a mensagem pro dono da conversa (se estiver online) e pra sala
    "admins" inteira, pra qualquer admin conectado ver a atualização na inbox
    sem precisar ter aberto aquela conversa especificamente."""
    payload = {"thread_id": thread_id, "mensagem": mensagem}
    socketio.emit("suporte:nova", payload, room=_suporte_room(usuario_id))
    socketio.emit("suporte:nova", payload, room="admins")


def broadcast_suporte_encerrado(usuario_id, thread):
    """Avisa o operador (se estiver online) que a conversa foi encerrada, pra
    UI dele abrir o formulário de avaliação na hora."""
    socketio.emit("suporte:encerrado", thread, room=_suporte_room(usuario_id))


@socketio.on("connect")
def handle_connect():
    # Conexão anônima é permitida (widget público de chat, sem login de CRM
    # nem de indicador) — só quem tem sessão de usuário do CRM entra em "admins"
    # e é rastreado na presença online/offline.
    user = _current_user_row()
    if user is not None:
        presence.mark_online(user["id"], request.sid)
        join_room(_suporte_room(user["id"]))
        if user["papel"] == "admin":
            join_room("admins")
        _broadcast_presence()


@socketio.on("disconnect")
def handle_disconnect():
    presence.mark_offline_by_sid(request.sid)
    _broadcast_presence()


@socketio.on("join_indicacao")
def handle_join_indicacao(data):
    """Entra na sala de chat de uma indicação. Operador do CRM (sessão de
    usuário) informa `indicacao_id` direto; o cliente anônimo que clicou no
    link só entra se souber o `chat_token` daquela indicação específica."""
    if not isinstance(data, dict):
        return
    db = get_db()
    user = _current_user_row()
    row = None
    if user is not None and data.get("indicacao_id") is not None:
        row = db.execute("SELECT id FROM indicacoes WHERE id = ?", (data["indicacao_id"],)).fetchone()
    elif data.get("chat_token"):
        row = db.execute("SELECT id FROM indicacoes WHERE chat_token = ?", (data["chat_token"],)).fetchone()
    if row is not None:
        join_room(_indicacao_room(row["id"]))
