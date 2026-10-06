from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationType


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def add(
        db: Session,
        *,
        user_id: int,
        type_notification: NotificationType | str,
        titre: str,
        message: str,
        reservation_id: int | None = None,
        depart_id: int | None = None,
        canal: NotificationChannel | str = NotificationChannel.PUSH,
    ) -> Notification:
        item = Notification(
            id_user=user_id,
            type_notification=getattr(type_notification, "value", str(type_notification)),
            titre=titre,
            message=message,
            id_reservation=reservation_id,
            id_depart=depart_id,
            canal=getattr(canal, "value", str(canal)),
        )
        db.add(item)
        return item

    def list_for_user(self, user_id: int, *, page: int = 1, page_size: int = 20, unread_only: bool = False):
        statement = select(Notification).where(Notification.id_user == user_id)
        if unread_only:
            statement = statement.where(Notification.est_lue.is_(False))
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(self.db.scalars(statement.order_by(Notification.date_envoi.desc(), Notification.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size if total else 0}

    def mark_read(self, notification_id: int, user_id: int) -> Notification:
        item = self.db.scalar(select(Notification).where(Notification.id == notification_id, Notification.id_user == user_id))
        if not item:
            from fastapi import HTTPException
            raise HTTPException(404, "Notification introuvable.")
        item.est_lue = True
        item.date_lecture = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item
