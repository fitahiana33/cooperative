from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.cooperative import Cooperative, GareCooperative, CooperativeMember

class CooperativeRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, cooperative_id: int) -> Cooperative | None:
        return self.db.get(Cooperative, cooperative_id)

    def find_by_nom(self, nom: str) -> Cooperative | None:
        return self.db.scalar(select(Cooperative).where(Cooperative.nom == nom.strip()))

    def create(self, cooperative: Cooperative) -> Cooperative:
        self.db.add(cooperative)
        self.db.commit()
        self.db.refresh(cooperative)
        return cooperative

    def update(self, cooperative: Cooperative) -> Cooperative:
        self.db.commit()
        self.db.refresh(cooperative)
        return cooperative

    def delete(self, cooperative: Cooperative) -> None:
        self.db.delete(cooperative)
        self.db.commit()
