from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_user_cooperative_ids, has_global_cooperative_access, require_permission
from app.db.session import get_db
from app.models.user import User
from app.services.dashboard import DashboardService

router = APIRouter(tags=["dashboard"])


def _scope(db: Session, user: User) -> set[int] | None:
    return None if has_global_cooperative_access(user) else get_user_cooperative_ids(db, user)


@router.get("/dashboard/summary")
def dashboard_summary(current_user: User = Depends(require_permission("DASHBOARD_READ")), db: Session = Depends(get_db)):
    return DashboardService(db).summary(cooperative_ids=_scope(db, current_user))


@router.get("/statistiques")
def statistics(
    date_from: date | None = None, date_to: date | None = None,
    current_user: User = Depends(require_permission("STATISTIQUE_READ")), db: Session = Depends(get_db),
):
    if date_from and date_to and date_to < date_from:
        from fastapi import HTTPException
        raise HTTPException(422, "La date de fin ne peut pas être antérieure à la date de début.")
    return DashboardService(db).statistics(date_from=date_from, date_to=date_to, cooperative_ids=_scope(db, current_user))


@router.post("/notifications/reminders")
def generate_reminders(current_user: User = Depends(require_permission("NOTIFICATION_MANAGE")), db: Session = Depends(get_db)):
    return {"created": DashboardService(db).generate_reminders()}

