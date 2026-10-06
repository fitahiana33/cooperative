from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.system import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.post("/reset-business-data")
def reset_business_data(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    result = SystemService(db).reset_business_data(current_user.id)
    return {"message": "Les données métier ont été réinitialisées.", **result}
