from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.authentication.password import verify_password
from app.services.system import SystemService

router = APIRouter(prefix="/system", tags=["system"])


class ResetBusinessDataRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


@router.post("/reset-business-data")
def reset_business_data(
    data: ResetBusinessDataRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    if not settings.is_development:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La réinitialisation n'est disponible qu'en environnement de développement.")
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mot de passe incorrect.")
    result = SystemService(db).reset_business_data(current_user.id)
    return {"message": "Les données métier ont été réinitialisées.", **result}
