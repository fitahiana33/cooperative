from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.authentication.token import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'accès invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = payload.get("sub")
    if not subject or not str(subject).isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contenu du jeton invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository(db).find_by_id(int(subject))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte utilisateur introuvable ou désactivé.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        assigned = {role.libelle for role in current_user.roles if role.is_active}
        if current_user.role not in allowed_roles and not assigned.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôle(s) requis: {', '.join(allowed_roles)}.",
            )
        return current_user

    return role_checker


def require_permission(code: str) -> Callable[[User], User]:
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.ADMIN:
            return current_user
        permissions = {
            permission.code
            for role in current_user.roles if role.is_active
            for permission in role.permissions if permission.is_active
        }
        if code not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission requise: {code}.")
        return current_user
    return permission_checker


require_admin = require_roles(UserRole.ADMIN)
require_staff = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.DRIVER)
