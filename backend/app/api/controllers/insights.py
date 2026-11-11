from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_user_cooperative_ids, has_global_cooperative_access, require_permission, station_agent_scope
from app.core.clock import local_today
from app.db.session import get_db
from app.models.user import User
from app.services.insights import DecisionSupportService

router = APIRouter(prefix="/aide-decision", tags=["decision-support"])


@router.get("")
def decision_support(date_reference: date | None = None, current_user: User = Depends(require_permission("AIDE_DECISION_READ")), db: Session = Depends(get_db)):
    if date_reference and date_reference > local_today():
        raise HTTPException(422, "La date de référence ne peut pas être future.")
    if date_reference and date_reference.year < 2000:
        raise HTTPException(422, "La date de référence doit être postérieure au 1er janvier 2000.")
    scope = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return DecisionSupportService(db, gare_ids=station_agent_scope(db, current_user)).analyze(date_from=date_reference, cooperative_ids=scope)
