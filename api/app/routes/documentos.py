import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from app.auth import log_activity, require_login
from app.db import get_db
from app.errors import ApiError
from app.pagination import paginate_query

bp = Blueprint("documentos", __name__, url_prefix="/api/v1/documentos")
bp.before_request(require_login)

CAMPOS_EDITAVEIS = ["categoria"]


def _documentos_dir():
    path = Path(current_app.config["DOCUMENTOS_DIR"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def _row_to_dict(row):
    return dict(row)


def _get_or_404(db, documento_id):
    row = db.execute("SELECT * FROM documentos WHERE id = ?", (documento_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Documento {documento_id} não encontrado", 404)
    return row


def _assert_projeto_exists(db, projeto_id):
    row = db.execute("SELECT id FROM projetos WHERE id = ?", (projeto_id,)).fetchone()
    if row is None:
        raise ApiError("NOT_FOUND", f"Projeto {projeto_id} não encontrado", 404)


@bp.get("")
def list_documentos():
    db = get_db()
    filters, params = [], []

    if projeto_id := request.args.get("projeto_id"):
        filters.append("projeto_id = ?")
        params.append(projeto_id)
    if categoria := request.args.get("categoria"):
        filters.append("categoria = ?")
        params.append(categoria)
    if extensao := request.args.get("extensao"):
        filters.append("extensao = ?")
        params.append(extensao)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows, pagination = paginate_query(
        db,
        f"SELECT * FROM documentos {where} ORDER BY id",
        f"SELECT COUNT(*) FROM documentos {where}",
        params,
    )
    return jsonify({"data": [_row_to_dict(r) for r in rows], "pagination": pagination})


@bp.get("/<int:documento_id>")
def get_documento(documento_id):
    db = get_db()
    return jsonify(_row_to_dict(_get_or_404(db, documento_id)))


@bp.get("/<int:documento_id>/arquivo")
def download_documento(documento_id):
    db = get_db()
    row = _get_or_404(db, documento_id)
    diretorio = _documentos_dir() / str(row["projeto_id"])
    caminho = Path(row["caminho_relativo"])
    return send_from_directory(diretorio, caminho.name, as_attachment=True, download_name=row["nome_arquivo"])


@bp.post("")
def create_documento():
    projeto_id = request.form.get("projeto_id")
    categoria = request.form.get("categoria")
    arquivo = request.files.get("arquivo")

    if not projeto_id:
        raise ApiError("VALIDATION_ERROR", "Campo 'projeto_id' é obrigatório", 400)
    if not categoria:
        raise ApiError("VALIDATION_ERROR", "Campo 'categoria' é obrigatório", 400)
    if arquivo is None or arquivo.filename == "":
        raise ApiError("VALIDATION_ERROR", "Envie um arquivo no campo 'arquivo'", 400)

    db = get_db()
    _assert_projeto_exists(db, projeto_id)

    nome_original = secure_filename(arquivo.filename) or arquivo.filename
    extensao = nome_original.rsplit(".", 1)[-1].lower() if "." in nome_original else None
    nome_armazenado = f"{uuid.uuid4().hex}.{extensao}" if extensao else uuid.uuid4().hex

    pasta_projeto = _documentos_dir() / str(projeto_id)
    pasta_projeto.mkdir(parents=True, exist_ok=True)
    destino = pasta_projeto / nome_armazenado
    arquivo.save(destino)
    tamanho_bytes = destino.stat().st_size

    cur = db.execute(
        """INSERT INTO documentos (projeto_id, categoria, nome_arquivo, extensao, tamanho_bytes, caminho_relativo)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (projeto_id, categoria, arquivo.filename, extensao, tamanho_bytes, nome_armazenado),
    )
    db.commit()
    log_activity(db, "create", "documentos", cur.lastrowid, f"Documento {arquivo.filename} enviado")
    row = db.execute("SELECT * FROM documentos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_row_to_dict(row)), 201


@bp.patch("/<int:documento_id>")
def update_documento(documento_id):
    db = get_db()
    _get_or_404(db, documento_id)
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in CAMPOS_EDITAVEIS}

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = [*updates.values(), documento_id]
        db.execute(
            f"UPDATE documentos SET {set_clause}, atualizado_em = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
            params,
        )
        db.commit()
        log_activity(db, "update", "documentos", documento_id, f"Documento #{documento_id} atualizado")

    row = db.execute("SELECT * FROM documentos WHERE id = ?", (documento_id,)).fetchone()
    return jsonify(_row_to_dict(row))


@bp.delete("/<int:documento_id>")
def delete_documento(documento_id):
    db = get_db()
    row = _get_or_404(db, documento_id)

    arquivo = _documentos_dir() / str(row["projeto_id"]) / row["caminho_relativo"]
    arquivo.unlink(missing_ok=True)

    db.execute("DELETE FROM documentos WHERE id = ?", (documento_id,))
    db.commit()
    log_activity(db, "delete", "documentos", documento_id, f"Documento #{documento_id} excluído")
    return "", 204
