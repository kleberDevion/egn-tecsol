from flask import g, session

from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
from app.errors import ApiError


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def get_current_user():
    if "user" in g:
        return g.user

    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return None

    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE id = ? AND ativo = 1", (user_id,)).fetchone()
    g.user = dict(row) if row is not None else None
    return g.user


def require_login():
    if get_current_user() is None:
        raise ApiError("UNAUTHORIZED", "Login necessário", 401)


def require_admin():
    require_login()
    if g.user["papel"] != "admin":
        raise ApiError("FORBIDDEN", "Acesso restrito a administradores", 403)


def foto_url(user_row):
    if not user_row or not user_row["foto_path"]:
        return None
    return f"/api/v1/auth/foto/{user_row['id']}"


def user_grupos(db, usuario_id):
    rows = db.execute(
        "SELECT grupo_chave FROM usuario_grupos WHERE usuario_id = ? ORDER BY grupo_chave", (usuario_id,)
    ).fetchall()
    return [row["grupo_chave"] for row in rows]


def set_user_grupos(db, usuario_id, grupos_chaves):
    validas = {row["chave"] for row in db.execute("SELECT chave FROM grupos").fetchall()}
    invalidas = [g for g in grupos_chaves if g not in validas]
    if invalidas:
        raise ApiError("VALIDATION_ERROR", f"Grupo(s) inválido(s): {', '.join(invalidas)}", 400)
    db.execute("DELETE FROM usuario_grupos WHERE usuario_id = ?", (usuario_id,))
    db.executemany(
        "INSERT INTO usuario_grupos (usuario_id, grupo_chave) VALUES (?, ?)",
        [(usuario_id, g) for g in dict.fromkeys(grupos_chaves)],
    )


def log_activity(db, acao, entidade=None, entidade_id=None, descricao=None):
    user = get_current_user()
    db.execute(
        "INSERT INTO activity_log (usuario_id, acao, entidade, entidade_id, descricao) VALUES (?, ?, ?, ?, ?)",
        (user["id"] if user else None, acao, entidade, entidade_id, descricao),
    )
    db.commit()
