from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.embarquement import Embarquement

class EmbarquementRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, id_embarquement: int) -> Embarquement | None:
        return self.db.get(Embarquement, id_embarquement)

    def find_by_billet(self, id_billet: int) -> Embarquement | None:
        return self.db.scalar(select(Embarquement).where(Embarquement.id_billet == id_billet))

    def create(self, embarquement: Embarquement) -> Embarquement:
        self.db.add(embarquement)
        self.db.commit()
        self.db.refresh(embarquement)
        return embarquement

    def update(self, embarquement: Embarquement) -> Embarquement:
        self.db.commit()
        self.db.refresh(embarquement)
        return embarquement

    def delete(self, embarquement: Embarquement) -> None:
        self.db.delete(embarquement)
        self.db.commit()
