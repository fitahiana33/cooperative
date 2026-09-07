from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Role, Permission, User
from app.core.pagination import paginate
from app.models.user import UserRole
from app.core.roles import normalize_role

class RoleService:
    def __init__(self, db: Session):
        self.db = db

    # --- Role CRUD ---
    def list_roles(self, *, page=1, page_size=20, search=None, sort_by="libelle", sort_order="asc"):
        return paginate(self.db, Role, page=page, page_size=page_size, search=search, search_fields=("libelle", "description"), sort_by=sort_by, sort_fields=("libelle", "created_at"), sort_order=sort_order)

    def get_role(self, role_id: int) -> Role:
        role = self.db.get(Role, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Rôle introuvable.")
        return role

    @staticmethod
    def _is_admin(role: Role) -> bool:
        return normalize_role(role.libelle) == UserRole.ADMIN

    def _protect_admin_role(self, role: Role, *, active: bool | None = None) -> None:
        if self._is_admin(role) and active is False:
            raise HTTPException(
                status_code=409,
                detail="Le rôle administrateur système ne peut pas être désactivé.",
            )

    def create_role(self, libelle: str, description: str | None = None) -> Role:
        normalized_label = normalize_role(libelle)
        if not normalized_label:
            raise HTTPException(status_code=422, detail="Le libellé du rôle est obligatoire.")
        existing = self.db.scalar(select(Role).where(func.lower(Role.libelle) == normalized_label))
        if existing:
            raise HTTPException(status_code=400, detail="Un rôle avec ce libellé existe déjà.")
        role = Role(libelle=normalized_label, description=description.strip() if description else None)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update_role(self, role_id: int, libelle: str | None = None, description: str | None = None, is_active: bool | None = None) -> Role:
        role = self.get_role(role_id)
        self._protect_admin_role(role, active=is_active)
        if libelle and normalize_role(libelle) != normalize_role(role.libelle):
            normalized_label = normalize_role(libelle)
            existing = self.db.scalar(select(Role).where(func.lower(Role.libelle) == normalized_label))
            if existing:
                raise HTTPException(status_code=400, detail="Un rôle avec ce libellé existe déjà.")
            if self._is_admin(role):
                raise HTTPException(status_code=409, detail="Le rôle administrateur système ne peut pas être renommé.")
            role.libelle = normalized_label
        if description is not None:
            role.description = description
        if is_active is not None:
            role.is_active = is_active
        self.db.commit()
        self.db.refresh(role)
        return role

    def toggle_role(self, role_id: int) -> Role:
        role = self.get_role(role_id)
        self._protect_admin_role(role, active=not role.is_active)
        role.is_active = not role.is_active
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role_id: int) -> None:
        role = self.get_role(role_id)
        if self._is_admin(role):
            raise HTTPException(status_code=409, detail="Le rôle administrateur système ne peut pas être supprimé.")
        if role.users:
            raise HTTPException(status_code=400, detail="Impossible de supprimer un rôle attribué à des utilisateurs.")
        self.db.delete(role)
        self.db.commit()

    # --- Permission CRUD ---
    def list_permissions(self, *, page=1, page_size=20, search=None, sort_by="code", sort_order="asc"):
        return paginate(self.db, Permission, page=page, page_size=page_size, search=search, search_fields=("code", "libelle", "module"), sort_by=sort_by, sort_fields=("code", "module", "created_at"), sort_order=sort_order)

    def get_permission(self, permission_id: int) -> Permission:
        perm = self.db.get(Permission, permission_id)
        if not perm:
            raise HTTPException(status_code=404, detail="Permission introuvable.")
        return perm

    def create_permission(self, code: str, libelle: str, module: str, description: str | None = None) -> Permission:
        normalized_code = code.strip().upper()
        existing = self.db.scalar(select(Permission).where(func.upper(Permission.code) == normalized_code))
        if existing:
            raise HTTPException(status_code=400, detail="Une permission avec ce code existe déjà.")
        perm = Permission(
            code=normalized_code,
            libelle=libelle.strip(),
            module=module.strip().upper(),
            description=description,
        )
        self.db.add(perm)
        self.db.commit()
        self.db.refresh(perm)
        return perm

    def update_permission(self, permission_id: int, code: str | None = None, libelle: str | None = None, module: str | None = None, description: str | None = None, is_active: bool | None = None) -> Permission:
        perm = self.get_permission(permission_id)
        if code and code.strip().upper() != perm.code:
            existing = self.db.scalar(select(Permission).where(func.upper(Permission.code) == code.strip().upper()))
            if existing:
                raise HTTPException(status_code=400, detail="Une permission avec ce code existe déjà.")
            perm.code = code.strip().upper()
        if libelle is not None:
            perm.libelle = libelle.strip()
        if module is not None:
            perm.module = module.strip().upper()
        if description is not None:
            perm.description = description
        if is_active is not None:
            perm.is_active = is_active
        self.db.commit()
        self.db.refresh(perm)
        return perm

    def delete_permission(self, permission_id: int) -> None:
        perm = self.get_permission(permission_id)
        if perm.roles:
            raise HTTPException(status_code=400, detail="Impossible de supprimer une permission attribuée à un rôle.")
        self.db.delete(perm)
        self.db.commit()

    # --- Role ↔ Permission Assignments ---
    def assign_permission_to_role(self, role_id: int, permission_id: int) -> Role:
        role = self.get_role(role_id)
        perm = self.get_permission(permission_id)
        if not role.is_active or not perm.is_active:
            raise HTTPException(status_code=422, detail="Le rôle et la permission doivent être actifs.")
        if perm not in role.permissions:
            role.permissions.append(perm)
            self.db.commit()
            self.db.refresh(role)
        return role

    def revoke_permission_from_role(self, role_id: int, permission_id: int) -> Role:
        role = self.get_role(role_id)
        perm = self.get_permission(permission_id)
        if perm in role.permissions:
            role.permissions.remove(perm)
            self.db.commit()
            self.db.refresh(role)
        return role

    # --- User ↔ Role Assignments ---
    def assign_role_to_user(self, user_id: int, role_id: int) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        role = self.get_role(role_id)
        if not role.is_active:
            raise HTTPException(status_code=422, detail="Le rôle sélectionné est inactif.")
        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()
            self.db.refresh(user)
        return user

    def revoke_role_from_user(self, user_id: int, role_id: int) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        role = self.get_role(role_id)
        if role in user.roles:
            if self._is_admin(role) and sum(
                1
                for assigned_role in user.roles
                if assigned_role.is_active and self._is_admin(assigned_role)
            ) <= 1:
                raise HTTPException(status_code=409, detail="Le dernier rôle administrateur d'un utilisateur ne peut pas être retiré.")
            user.roles.remove(role)
            self.db.commit()
            self.db.refresh(user)
        return user

    # --- Permission Checking ---
    @staticmethod
    def user_has_permission(user: User, permission_code: str) -> bool:
        if user.role == UserRole.ADMIN:
            return True
        user_permissions = {
            perm.code
            for role in user.roles if role.is_active
            for perm in role.permissions if perm.is_active
        }
        return permission_code in user_permissions
