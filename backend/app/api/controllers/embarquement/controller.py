from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.embarquement import EmbarquementControl, EmbarquementRead
from app.services.embarquement import EmbarquementService

router = APIRouter(prefix="/embarquement", tags=["embarquement"])


@router.post("/controle", response_model=EmbarquementRead)
def control_ticket(
    data: EmbarquementControl,
    current_user: User = Depends(require_permission("EMBARQUEMENT_MANAGE")), db: Session = Depends(get_db),
):
    return EmbarquementService(db).control(code=data.code, agent=current_user, date_heure=data.date_heure)

