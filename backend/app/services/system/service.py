from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.user import User


class SystemService:
    _protected_tables = {"users", "roles", "permissions", "users_roles", "roles_permissions"}

    def __init__(self, db: Session):
        self.db = db

    def reset_business_data(self, admin_user_id: int) -> dict[str, int]:
        tables = sorted(
            table.name
            for table in Base.metadata.sorted_tables
            if table.name not in self._protected_tables
        )
        if tables:
            table_list = ", ".join(f'"{table}"' for table in tables)
            self.db.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))

        deleted_users = self.db.execute(
            text(
                """
                DELETE FROM users
                WHERE id_user <> :admin_user_id
                  AND id_user NOT IN (
                      SELECT ur.id_user
                      FROM users_roles ur
                      JOIN roles r ON r.id_role = ur.id_role
                      WHERE lower(r.libelle) = 'admin'
                  )
                """
            ),
            {"admin_user_id": admin_user_id},
        ).rowcount or 0
        self.db.commit()
        return {"tables_cleared": len(tables), "users_deleted": deleted_users}
