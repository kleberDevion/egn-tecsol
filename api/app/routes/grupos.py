from flask import Blueprint, jsonify

from app.auth import require_login
from app.db import get_db

bp = Blueprint("grupos", __name__, url_prefix="/api/v1/grupos")
bp.before_request(require_login)


@bp.get("")
def list_grupos():
    db = get_db()
    rows = db.execute("SELECT * FROM grupos ORDER BY ordem").fetchall()
    return jsonify({"data": [dict(r) for r in rows]})
