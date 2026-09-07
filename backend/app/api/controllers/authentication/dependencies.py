from datetime import date
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.authentication import RevokedToken
from app.models.chauffeur import Chauffeur
from app.models.cooperative import Cooperative, CooperativeMember
from app.models.vehicule import Vehicule, VehiculeDocument
from app.repositories.user import UserRepository
from app.services.authentication.token import decode_access_token
from app.core.roles import normalize_role

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

    if db.get(RevokedToken, payload.get("jti")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton révoqué.",
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
        allowed = {normalize_role(role) for role in allowed_roles}
        assigned = {normalize_role(role.libelle) for role in current_user.roles if role.is_active}
        if normalize_role(current_user.role) not in allowed and not assigned.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôle(s) requis: {', '.join(allowed_roles)}.",
            )
        return current_user

    return role_checker


def require_permission(code: str) -> Callable[[User], User]:
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if has_active_role(current_user, UserRole.ADMIN):
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


def has_active_role(user: User, role: str) -> bool:
    expected = normalize_role(role)
    return any(
        normalize_role(assigned_role.libelle) == expected
        for assigned_role in user.roles
        if assigned_role.is_active
    )


def has_global_cooperative_access(user: User) -> bool:
    """Return whether the user may inspect all cooperative-owned resources."""
    return has_active_role(user, UserRole.ADMIN) or has_active_role(
        user,
        UserRole.RESPONSABLE_GARE,
    )


def get_user_cooperative_ids(db: Session, user: User) -> set[int]:
    """Return active cooperative memberships plus cooperatives managed by user."""
    today = date.today()
    member_ids = db.scalars(
        select(CooperativeMember.id_cooperative).where(
            CooperativeMember.id_user == user.id,
            CooperativeMember.is_active.is_(True),
            or_(
                CooperativeMember.date_adhesion.is_(None),
                CooperativeMember.date_adhesion <= today,
            ),
            or_(
                CooperativeMember.date_fin.is_(None),
                CooperativeMember.date_fin >= today,
            ),
        )
    )
    responsible_ids = db.scalars(
        select(Cooperative.id).where(Cooperative.responsable_id == user.id)
    )
    return set(member_ids).union(responsible_ids)


def ensure_cooperative_access(db: Session, user: User, cooperative_id: int) -> None:
    if has_global_cooperative_access(user):
        return
    if cooperative_id not in get_user_cooperative_ids(db, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à accéder à cette coopérative.",
        )


def ensure_vehicule_access(db: Session, user: User, vehicule_id: int) -> Vehicule:
    vehicule = db.get(Vehicule, vehicule_id)
    if not vehicule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Véhicule introuvable.")
    ensure_cooperative_access(db, user, vehicule.id_cooperative)
    return vehicule


def ensure_chauffeur_access(db: Session, user: User, chauffeur_id: int) -> Chauffeur:
    chauffeur = db.get(Chauffeur, chauffeur_id)
    if not chauffeur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chauffeur introuvable.")
    ensure_cooperative_access(db, user, chauffeur.id_cooperative)
    return chauffeur


def ensure_document_access(db: Session, user: User, document_id: int) -> VehiculeDocument:
    document = db.get(VehiculeDocument, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")
    ensure_vehicule_access(db, user, document.id_vehicule)
    return document


require_admin = require_roles(UserRole.ADMIN)
require_staff = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.DRIVER)
