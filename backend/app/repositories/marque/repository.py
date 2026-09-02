from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.marque import Marque

class MarqueRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, marque_id: int) -> Marque | None:
        return self.db.get(Marque, marque_id)

    def find_by_nom(self, nom: str) -> Marque | None:
        return self.db.scalar(select(Marque).where(Marque.nom == nom.strip()))

    def create(self, marque: Marque) -> Marque:
        self.db.add(marque)
        self.db.commit()
        self.db.refresh(marque)
        return marque

    def update(self, marque: Marque) -> Marque:
        self.db.commit()
        self.db.refresh(marque)
        return marque

    def delete(self, marque: Marque) -> None:
        self.db.delete(marque)
        self.db.commit()
