from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.billet import Billet


class BilletRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, id_billet: int) -> Billet | None:
        return self.db.get(Billet, id_billet)

    def find_by_numero(self, numero_billet: str) -> Billet | None:
        return self.db.scalar(select(Billet).where(Billet.numero_billet == numero_billet.strip()))

    def find_by_qr_uuid(self, qr_code_uuid: UUID) -> Billet | None:
        return self.db.scalar(select(Billet).where(Billet.qr_code_uuid == qr_code_uuid))

    def create(self, billet: Billet) -> Billet:
        self.db.add(billet)
        self.db.commit()
        self.db.refresh(billet)
        return billet

    def update(self, billet: Billet) -> Billet:
        self.db.commit()
        self.db.refresh(billet)
        return billet

    def delete(self, billet: Billet) -> None:
        self.db.delete(billet)
        self.db.commit()
