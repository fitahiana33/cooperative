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
               after: dict | None = None, description: str | None = None, gare_id: int | None = None, cooperative_id: int | None = None) -> AuditLog:
        if entity_id is not None and str(entity_id).isdigit() and gare_id is None:
            from app.models.depart import Depart
            from app.models.reservation import Reservation
            from app.models.finance import Paiement, Caisse
            depart = None
            if entity_type == "depart":
                depart = self.db.get(Depart, int(entity_id))
            elif entity_type == "reservation":
                item = self.db.get(Reservation, int(entity_id))
                depart = getattr(item, "depart", None) if item else None
            elif entity_type == "paiement":
                item = self.db.get(Paiement, int(entity_id))
                depart = getattr(getattr(item, "reservation", None), "depart", None) if item else None
            elif entity_type == "caisse":
                item = self.db.get(Caisse, int(entity_id))
                gare_id = item.id_gare if item else None
            if depart:
                gare_id, cooperative_id = depart.id_gare, depart.id_cooperative
        item = AuditLog(
            id_gare=gare_id, id_cooperative=cooperative_id,
            id_user=user_id, action=action, entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            before_data=_jsonable(before), after_data=_jsonable(after), description=description,
        )
        self.db.add(item)
        return item

    def list(self, *, page: int = 1, page_size: int = 50, action: str | None = None,
             entity_type: str | None = None, user_id: int | None = None,
             gare_ids: set[int] | None = None, cooperative_ids: set[int] | None = None):
        statement = select(AuditLog)
        if gare_ids is not None:
            statement = statement.where(AuditLog.id_gare.in_(gare_ids))
        if cooperative_ids is not None:
            statement = statement.where(AuditLog.id_cooperative.in_(cooperative_ids))
        if action:
            statement = statement.where(AuditLog.action == action)
        if entity_type:
            statement = statement.where(AuditLog.entity_type == entity_type)
        if user_id:
            statement = statement.where(AuditLog.id_user == user_id)
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(self.db.scalars(statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size if total else 0}
