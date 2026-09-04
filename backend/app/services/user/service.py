import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.role import Role
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.services.authentication.password import hash_password
from app.core.roles import normalize_role

logger = logging.getLogger("cooperative.user")


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def list_users(self) -> list[User]:
        return self.repository.list()

    def create_user(self, data: UserCreate) -> User:
        name = data.name.strip()
        first_name = data.first_name.strip()
        email = str(data.email).strip().lower()
        if not name or not first_name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Le nom et le prénom sont obligatoires.")
        user = User(
            name=name,
            first_name=first_name,
            email=email,
            telephone=data.telephone.strip() if data.telephone else None,
            address=data.address.strip() if data.address else None,
            password_hash=hash_password(data.password),
        )
        role_name = normalize_role(data.role or UserRole.PASSAGER)
        role = self.repository.db.query(Role).filter(Role.libelle == role_name).first()
        if not role or not role.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rôle inconnu: {role_name}.")
        user.roles.append(role)
        try:
            return self.repository.create(user)
        except IntegrityError:
            self.repository.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette adresse email est déjà utilisée.")
        except Exception:
            self.repository.db.rollback()
            logger.exception("Erreur interne création utilisateur email=%s", email)
            raise HTTPException(status_code=500, detail="Une erreur est survenue lors de la création de l'utilisateur.")

    def update_user(self, user_id: int, **fields) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        if fields.get("email"):
            email = str(fields["email"]).lower().strip()
            existing = self.repository.find_by_email(email)
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail="Cette adresse email est déjà utilisée.")
            user.email = email
        if fields.get("password"):
            user.password_hash = hash_password(fields["password"])
        for key in ("name", "first_name", "telephone", "address", "is_active"):
            if key in fields and fields[key] is not None:
                setattr(user, key, fields[key].strip() if isinstance(fields[key], str) else fields[key])
        try:
            return self.repository.update(user)
        except IntegrityError:
            self.repository.db.rollback()
            raise HTTPException(status_code=409, detail="Les informations utilisateur sont déjà utilisées.")
        except Exception:
            self.repository.db.rollback()
            logger.exception("Erreur interne modification utilisateur id=%s", user_id)
            raise HTTPException(status_code=500, detail="Une erreur est survenue lors de la modification de l'utilisateur.")

    def delete_user(self, user_id: int) -> None:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        try:
            self.repository.db.delete(user)
            self.repository.db.commit()
        except IntegrityError:
            self.repository.db.rollback()
            raise HTTPException(status_code=400, detail="Impossible de supprimer cet utilisateur.")
