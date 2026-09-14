from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.destination import Destination


class DestinationRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, destination_id: int) -> Destination | None:
        return self.db.get(Destination, destination_id)

    def find_by_nom(self, nom: str) -> Destination | None:
        return self.db.scalar(select(Destination).where(Destination.nom == nom.strip()))

    def create(self, destination: Destination) -> Destination:
        self.db.add(destination)
        self.db.commit()
        self.db.refresh(destination)
        return destination

    def update(self, destination: Destination) -> Destination:
        self.db.commit()
        self.db.refresh(destination)
        return destination

    def delete(self, destination: Destination) -> None:
        self.db.delete(destination)
        self.db.commit()
