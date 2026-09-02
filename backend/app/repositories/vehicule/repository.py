from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.vehicule import Vehicule, VehiculeDocument, VehiculeChauffeur

class VehiculeRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, vehicule_id: int) -> Vehicule | None:
        return self.db.get(Vehicule, vehicule_id)

    def find_by_immatriculation(self, immatriculation: str) -> Vehicule | None:
        return self.db.scalar(select(Vehicule).where(Vehicule.immatriculation == immatriculation.strip()))

    def create(self, vehicule: Vehicule) -> Vehicule:
        self.db.add(vehicule)
        self.db.commit()
        self.db.refresh(vehicule)
        return vehicule

    def update(self, vehicule: Vehicule) -> Vehicule:
        self.db.commit()
        self.db.refresh(vehicule)
        return vehicule

    def delete(self, vehicule: Vehicule) -> None:
        self.db.delete(vehicule)
        self.db.commit()
