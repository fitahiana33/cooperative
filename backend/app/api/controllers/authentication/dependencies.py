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
from app.models.cooperative import Cooperative, CooperativeMember, GareCooperative
from app.models.gare import GareAgent
from app.models.vehicule import Vehicule, VehiculeChauffeur, VehiculeDocument
from app.repositories.user import UserRepository
from app.services.authentication.token import decode_access_token
from app.core.roles import normalize_role
from app.core.clock import local_today

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
    if user.token_is_stale(payload.get("iat")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le mot de passe a été modifié. Reconnectez-vous.",
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


def ensure_admin_protected(actor: User, *, target: User | None = None, role_name: str | None = None) -> None:
    """Only an administrator may create, change or grant administrator accounts.

    USER_* and ROLE_MANAGE can be delegated; without this guard a delegated
    user could take over an admin account or make themselves admin.
    """
    if has_active_role(actor, UserRole.ADMIN):
        return
    target_is_admin = target is not None and has_active_role(target, UserRole.ADMIN)
    granting_admin = role_name is not None and normalize_role(role_name) == UserRole.ADMIN
    if target_is_admin or granting_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur peut gérer un compte ou un rôle administrateur.")


def has_permission(user: User, code: str) -> bool:
    if has_active_role(user, UserRole.ADMIN):
        return True
    return any(
        permission.code == code and permission.is_active
        for role in user.roles if role.is_active
        for permission in role.permissions
    )


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


STAFF_ROLES = (UserRole.AGENT_GARE, UserRole.RESPONSABLE_COOPERATIVE, UserRole.CHAUFFEUR)


def is_staff(user: User) -> bool:
    """Staff roles take precedence over the passenger role every user may also hold."""
    return any(has_active_role(user, role) for role in STAFF_ROLES)


def resolve_owner_scope(db: Session, user: User) -> tuple[int | None, set[int] | None]:
    """Scope for reservations and tickets: (owner id, cooperative ids).

    Global roles see everything; staff see their cooperatives; a passenger
    only sees what they booked.
    """
    if has_global_cooperative_access(user):
        return None, None
    if is_staff(user):
        return None, get_user_cooperative_ids(db, user)
    if has_active_role(user, UserRole.PASSAGER):
        return user.id, None
    return None, set()


def _assigned_gare_ids(db: Session, user: User) -> set[int]:
    return set(db.scalars(select(GareAgent.id_gare).where(GareAgent.id_user == user.id)))


def get_user_cooperative_ids(db: Session, user: User) -> set[int]:
    """Cooperatives the user may act on.

    Active memberships, cooperatives they manage, and the cooperatives
    operating at the stations they are attached to as agent.
    """
    today = local_today()
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
    station_ids = _assigned_gare_ids(db, user)
    station_cooperative_ids = db.scalars(
        select(GareCooperative.id_cooperative).where(
            GareCooperative.id_gare.in_(station_ids),
            GareCooperative.is_active.is_(True),
            or_(GareCooperative.date_debut.is_(None), GareCooperative.date_debut <= today),
            or_(GareCooperative.date_fin.is_(None), GareCooperative.date_fin >= today),
        )
    ) if station_ids else []
    return set(member_ids).union(responsible_ids).union(station_cooperative_ids)


def get_user_gare_ids(db: Session, user: User) -> set[int] | None:
    """Stations the user may act on: their own stations, plus those of their cooperatives."""
    if has_global_cooperative_access(user):
        return None
    assigned = _assigned_gare_ids(db, user)
    if assigned and has_active_role(user, UserRole.AGENT_GARE):
        # An agent works at their station only, not at every station of its cooperatives.
        return assigned
    cooperative_ids = get_user_cooperative_ids(db, user)
    if not cooperative_ids:
        return assigned
    today = local_today()
    gare_ids = db.scalars(
        select(GareCooperative.id_gare).where(
            GareCooperative.id_cooperative.in_(cooperative_ids),
            GareCooperative.is_active.is_(True),
            or_(GareCooperative.date_debut.is_(None), GareCooperative.date_debut <= today),
            or_(GareCooperative.date_fin.is_(None), GareCooperative.date_fin >= today),
        )
    )
    return set(gare_ids).union(assigned)


def ensure_gare_access(db: Session, user: User, gare_id: int) -> None:
    gare_ids = get_user_gare_ids(db, user)
    if gare_ids is not None and gare_id not in gare_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à accéder à cette gare.",
        )


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
    # A driver may always see the vehicle they are assigned to (writes need other permissions).
    driven = db.scalar(
        select(VehiculeChauffeur.id_vehicule)
        .join(Chauffeur, Chauffeur.id == VehiculeChauffeur.id_chauffeur)
        .where(VehiculeChauffeur.id_vehicule == vehicule_id, VehiculeChauffeur.is_active.is_(True), Chauffeur.id_user == user.id)
    )
    if driven is None:
        ensure_cooperative_access(db, user, vehicule.id_cooperative)
    return vehicule


def ensure_chauffeur_access(db: Session, user: User, chauffeur_id: int) -> Chauffeur:
    chauffeur = db.get(Chauffeur, chauffeur_id)
    if not chauffeur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chauffeur introuvable.")
    # A driver may always see their own profile (writes need other permissions).
    if chauffeur.id_user != user.id:
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
