from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.role import Role
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.services.authentication.password import hash_password


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def list_users(self) -> list[User]:
        return self.repository.list()

    def create_user(self, data: UserCreate) -> User:
        user = User(
            name=data.name,
            first_name=data.first_name,
            email=str(data.email),
            telephone=data.telephone,
            address=data.address,
            password_hash=hash_password(data.password),
        )
        role_name = data.role or UserRole.PASSENGER
        role = self.repository.db.query(Role).filter(Role.libelle == role_name).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rôle inconnu: {role_name}.")
        user.roles.append(role)
        return self.repository.create(user)
