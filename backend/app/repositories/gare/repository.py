from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.gare import Gare, Quai, Zone, Emplacement

class GareRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, gare_id: int) -> Gare | None:
        return self.db.get(Gare, gare_id)

    def find_by_nom(self, nom: str) -> Gare | None:
        return self.db.scalar(select(Gare).where(Gare.nom == nom.strip()))

    def create(self, gare: Gare) -> Gare:
        self.db.add(gare)
        self.db.commit()
        self.db.refresh(gare)
        return gare

    def update(self, gare: Gare) -> Gare:
        self.db.commit()
        self.db.refresh(gare)
        return gare

    def delete(self, gare: Gare) -> None:
        self.db.delete(gare)
        self.db.commit()
