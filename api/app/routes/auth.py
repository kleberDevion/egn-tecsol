from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request, send_from_directory, session

from app.auth import foto_url, hash_password, log_activity, require_login, user_grupos, verify_password
from app.db import get_db
from app.errors import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}


def _public_user(db, row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "papel": row["papel"],
        "grupos": user_grupos(db, row["id"]),
        "criado_em": row["criado_em"],
        "ultimo_login_em": row["ultimo_login_em"],
        "foto_url": foto_url(row),
    }


def _avatar_dir():
    path = Path(current_app.config["AVATAR_DIR"])
    path.mkdir(parents=True, exist_ok=True)
    return path


@bp.get("/setup-status")
def setup_status():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    return jsonify({"needs_setup": total == 0})


@bp.post("/setup")
def setup():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if total > 0:
        raise ApiError("CONFLICT", "Configuração inicial já foi concluída", 409)

    body = request.get_json(force=True, silent=True) or {}
    nome, email, senha = body.get("nome"), body.get("email"), body.get("senha")
    if not nome:
        raise ApiError("VALIDATION_ERROR", "Campo 'nome' é obrigatório", 400)
    if not email:
        raise ApiError("VALIDATION_ERROR", "Campo 'email' é obrigatório", 400)
    if not senha or len(senha) < 8:
        raise ApiError("VALIDATION_ERROR", "Senha deve ter ao menos 8 caracteres", 400)

    cur = db.execute(
        """INSERT INTO usuarios (nome, email, senha_hash, papel, ultimo_login_em)
           VALUES (?, ?, ?, 'admin', strftime('%Y-%m-%dT%H:%M:%SZ','now'))""",
        (nome, email, hash_password(senha)),
    )
    db.commit()
    session["user_id"] = cur.lastrowid
    log_activity(db, "login", descricao="Primeiro acesso: conta de administrador criada")
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_public_user(db, row)), 201


@bp.post("/login")
def login():
    body = request.get_json(force=True, silent=True) or {}
    email, senha = body.get("email"), body.get("senha")
    if not email or not senha:
        raise ApiError("VALIDATION_ERROR", "Informe e-mail e senha", 400)

    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE email = ? AND ativo = 1", (email,)).fetchone()
    if row is None or not verify_password(senha, row["senha_hash"]):
        raise ApiError("UNAUTHORIZED", "E-mail ou senha inválidos", 401)

    session["user_id"] = row["id"]
    db.execute(
        "UPDATE usuarios SET ultimo_login_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
        (row["id"],),
    )
    db.commit()
    log_activity(db, "login", descricao=f"Login de {row['nome']}")
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (row["id"],)).fetchone()
    return jsonify(_public_user(db, row))


@bp.post("/logout")
def logout():
    require_login()
    db = get_db()
    log_activity(db, "logout", descricao=f"Logout de {g.user['nome']}")
    session.clear()
    return "", 204


@bp.get("/me")
def me():
    require_login()
    return jsonify(_public_user(get_db(), g.user))


@bp.post("/change-password")
def change_password():
    require_login()
    body = request.get_json(force=True, silent=True) or {}
    senha_atual, senha_nova = body.get("senha_atual"), body.get("senha_nova")
    if not senha_atual or not senha_nova:
        raise ApiError("VALIDATION_ERROR", "Informe a senha atual e a nova senha", 400)
    if len(senha_nova) < 8:
        raise ApiError("VALIDATION_ERROR", "Nova senha deve ter ao menos 8 caracteres", 400)

    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (g.user["id"],)).fetchone()
    if not verify_password(senha_atual, row["senha_hash"]):
        raise ApiError("UNAUTHORIZED", "Senha atual incorreta", 401)

    db.execute(
        "UPDATE usuarios SET senha_hash = ?, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
        (hash_password(senha_nova), g.user["id"]),
    )
    db.commit()
    log_activity(db, "change_password", descricao="Senha alterada")
    return "", 204


@bp.post("/foto")
def upload_foto():
    require_login()
    arquivo = request.files.get("foto")
    if arquivo is None or arquivo.filename == "":
        raise ApiError("VALIDATION_ERROR", "Envie um arquivo de imagem no campo 'foto'", 400)

    extensao = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
    if extensao not in EXTENSOES_PERMITIDAS:
        raise ApiError("VALIDATION_ERROR", "Formato inválido. Use PNG, JPG ou WEBP.", 400)

    avatar_dir = _avatar_dir()
    for existente in avatar_dir.glob(f"{g.user['id']}.*"):
        existente.unlink()
    destino = avatar_dir / f"{g.user['id']}.{extensao}"
    arquivo.save(destino)

    db = get_db()
    db.execute(
        "UPDATE usuarios SET foto_path = ?, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
        (destino.name, g.user["id"]),
    )
    db.commit()
    log_activity(db, "update", "usuarios", g.user["id"], "Foto de perfil atualizada")
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (g.user["id"],)).fetchone()
    return jsonify(_public_user(db, row))


@bp.get("/foto/<int:usuario_id>")
def get_foto(usuario_id):
    require_login()
    db = get_db()
    row = db.execute("SELECT foto_path FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if row is None or not row["foto_path"]:
        raise ApiError("NOT_FOUND", "Foto não encontrada", 404)
    return send_from_directory(_avatar_dir(), row["foto_path"])
