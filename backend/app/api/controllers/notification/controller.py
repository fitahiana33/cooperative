from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.notification import NotificationRead
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PageResponse[NotificationRead])
def list_notifications(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), unread_only: bool = False,
    current_user: User = Depends(require_permission("NOTIFICATION_READ")), db: Session = Depends(get_db),
):
    return NotificationService(db).list_for_user(current_user.id, page=page, page_size=page_size, unread_only=unread_only)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(notification_id: int, current_user: User = Depends(require_permission("NOTIFICATION_READ")), db: Session = Depends(get_db)):
    return NotificationService(db).mark_read(notification_id, current_user.id)

