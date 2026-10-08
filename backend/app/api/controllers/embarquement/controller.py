from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import ensure_cooperative_access, require_permission
from app.db.session import get_db
from app.models.depart import Depart
from app.models.user import User
from app.schemas.embarquement import EmbarquementControl, EmbarquementRead
from app.services.embarquement import EmbarquementService

router = APIRouter(prefix="/embarquement", tags=["embarquement"])


@router.post("/controle", response_model=EmbarquementRead)
def control_ticket(
    data: EmbarquementControl,
    current_user: User = Depends(require_permission("EMBARQUEMENT_MANAGE")), db: Session = Depends(get_db),
):
    depart = db.get(Depart, data.id_depart)
    if not depart:
        raise HTTPException(404, "Départ introuvable.")
    ensure_cooperative_access(db, current_user, depart.id_cooperative)
    return EmbarquementService(db).control(code=data.code, agent=current_user, depart_id=depart.id)

