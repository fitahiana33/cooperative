from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def _jsonable(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(self, *, user_id: int | None, action: str, entity_type: str,
               entity_id: int | str | None = None, before: dict | None = None,
               after: dict | None = None, description: str | None = None) -> AuditLog:
        item = AuditLog(
            id_user=user_id, action=action, entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            before_data=_jsonable(before), after_data=_jsonable(after), description=description,
        )
        self.db.add(item)
        return item

    def list(self, *, page: int = 1, page_size: int = 50, action: str | None = None,
             entity_type: str | None = None, user_id: int | None = None):
        statement = select(AuditLog)
        if action:
            statement = statement.where(AuditLog.action == action)
        if entity_type:
            statement = statement.where(AuditLog.entity_type == entity_type)
        if user_id:
            statement = statement.where(AuditLog.id_user == user_id)
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(self.db.scalars(statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size if total else 0}
