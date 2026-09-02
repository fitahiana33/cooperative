from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.modele import Modele

class ModeleRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, modele_id: int) -> Modele | None:
        return self.db.get(Modele, modele_id)

    def find_by_marque_and_nom(self, id_marque: int, nom: str) -> Modele | None:
        return self.db.scalar(select(Modele).where(Modele.id_marque == id_marque, Modele.nom == nom.strip()))

    def list_by_marque(self, id_marque: int) -> list[Modele]:
        return list(self.db.scalars(select(Modele).where(Modele.id_marque == id_marque).order_by(Modele.nom)))

    def create(self, modele: Modele) -> Modele:
        self.db.add(modele)
        self.db.commit()
        self.db.refresh(modele)
        return modele

    def update(self, modele: Modele) -> Modele:
        self.db.commit()
        self.db.refresh(modele)
        return modele

    def delete(self, modele: Modele) -> None:
        self.db.delete(modele)
        self.db.commit()
