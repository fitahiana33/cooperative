from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_user_cooperative_ids, has_global_cooperative_access, require_permission
from app.db.session import get_db
from app.models.user import User
from app.services.insights import DecisionSupportService

router = APIRouter(prefix="/aide-decision", tags=["decision-support"])


@router.get("")
def decision_support(date_reference: date | None = None, current_user: User = Depends(require_permission("AIDE_DECISION_READ")), db: Session = Depends(get_db)):
    scope = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return DecisionSupportService(db).analyze(date_from=date_reference, cooperative_ids=scope)
