from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, id_notification: int) -> Notification | None:
        return self.db.get(Notification, id_notification)

    def find_by_user(self, id_user: int) -> list[Notification]:
        return list(self.db.scalars(select(Notification).where(Notification.id_user == id_user).order_by(Notification.date_envoi.desc())).all())

    def find_unread_by_user(self, id_user: int) -> list[Notification]:
        return list(self.db.scalars(select(Notification).where(Notification.id_user == id_user, Notification.est_lue == False).order_by(Notification.date_envoi.desc())).all())

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def update(self, notification: Notification) -> Notification:
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete(self, notification: Notification) -> None:
        self.db.delete(notification)
        self.db.commit()

    def mark_as_read(self, id_notification: int) -> Notification | None:
        notification = self.find_by_id(id_notification)
        if notification:
            notification.est_lue = True
            notification.date_lecture = datetime.utcnow()
            self.db.commit()
            self.db.refresh(notification)
        return notification
