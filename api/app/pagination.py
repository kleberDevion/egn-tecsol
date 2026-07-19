from flask import request

from app.errors import ApiError


def get_pagination_params():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        raise ApiError("VALIDATION_ERROR", "'page' e 'per_page' devem ser inteiros", 400)

    if page < 1:
        raise ApiError("VALIDATION_ERROR", "'page' deve ser >= 1", 400)
    if per_page < 1 or per_page > 100:
        raise ApiError("VALIDATION_ERROR", "'per_page' deve estar entre 1 e 100", 400)

    return page, per_page


def paginate_query(db, select_sql, count_sql, params):
    page, per_page = get_pagination_params()

    total_items = db.execute(count_sql, params).fetchone()[0]
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    offset = (page - 1) * per_page

    rows = db.execute(
        f"{select_sql} LIMIT ? OFFSET ?", [*params, per_page, offset]
    ).fetchall()

    pagination = {
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
    }
    return rows, pagination
