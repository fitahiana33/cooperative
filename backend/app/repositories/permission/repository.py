from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.permission import Permission

class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, permission_id: int) -> Permission | None:
        return self.db.get(Permission, permission_id)

    def find_by_code(self, code: str) -> Permission | None:
        return self.db.scalar(select(Permission).where(Permission.code == code.strip()))

    def list_all(self) -> list[Permission]:
        return list(self.db.scalars(select(Permission).order_by(Permission.code)))

    def create(self, permission: Permission) -> Permission:
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def update(self, permission: Permission) -> Permission:
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def delete(self, permission: Permission) -> None:
        self.db.delete(permission)
        self.db.commit()
