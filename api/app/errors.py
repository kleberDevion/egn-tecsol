import psycopg

from flask import jsonify


class ApiError(Exception):
    def __init__(self, code, message, status):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def error_response(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def _rollback():
    from flask import g

    db = g.get("db")
    if db is not None:
        db.rollback()


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(e):
        return error_response(e.code, e.message, e.status)

    @app.errorhandler(psycopg.IntegrityError)
    def handle_integrity_error(e):
        # No PostgreSQL a transação fica abortada depois do erro; sem o rollback
        # qualquer query seguinte na mesma conexão falharia.
        _rollback()
        return error_response("CONFLICT", str(e), 409)

    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response("NOT_FOUND", "Rota não encontrada", 404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response("METHOD_NOT_ALLOWED", "Método não permitido para esta rota", 405)
