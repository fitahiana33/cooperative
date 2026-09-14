from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.itineraire import Itineraire

class ItineraireRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, id_itineraire: int) -> Itineraire | None:
        return self.db.get(Itineraire, id_itineraire)

    def find_by_destinations(self, id_dest_depart: int, id_dest_arrivee: int) -> Itineraire | None:
        return self.db.scalar(select(Itineraire).where(Itineraire.id_dest_depart == id_dest_depart, Itineraire.id_dest_arrivee == id_dest_arrivee))

    def create(self, itineraire: Itineraire) -> Itineraire:
        self.db.add(itineraire)
        self.db.commit()
        self.db.refresh(itineraire)
        return itineraire

    def update(self, itineraire: Itineraire) -> Itineraire:
        self.db.commit()
        self.db.refresh(itineraire)
        return itineraire

    def delete(self, itineraire: Itineraire) -> None:
        self.db.delete(itineraire)
        self.db.commit()
