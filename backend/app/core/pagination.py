from math import ceil
from typing import Any
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

def paginate(db: Session, model: Any, *, page: int, page_size: int, search: str | None, search_fields: tuple[str, ...], sort_by: str, sort_fields: tuple[str, ...], sort_order: str):
    statement = select(model)
    if search and search.strip():
        term = f"%{search.strip()}%"
        fields = [getattr(model, name) for name in search_fields]
        statement = statement.where(or_(*(field.ilike(term) for field in fields)))
    column = getattr(model, sort_by if sort_by in sort_fields else sort_fields[0])
    statement = statement.order_by((asc if sort_order == "asc" else desc)(column))
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    items = list(db.scalars(statement.offset((page - 1) * page_size).limit(page_size)))
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}
