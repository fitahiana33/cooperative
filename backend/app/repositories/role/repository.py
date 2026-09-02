from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.role import Role

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, role_id: int) -> Role | None:
        return self.db.get(Role, role_id)

    def find_by_libelle(self, libelle: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.libelle == libelle.strip()))

    def list_all(self) -> list[Role]:
        return list(self.db.scalars(select(Role).order_by(Role.libelle)))

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update(self, role: Role) -> Role:
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role: Role) -> None:
        self.db.delete(role)
        self.db.commit()
