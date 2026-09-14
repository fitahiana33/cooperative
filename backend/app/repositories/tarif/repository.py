from datetime import date

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models.tarif import Tarif


class TarifRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, id_tarif: int) -> Tarif | None:
        return self.db.get(Tarif, id_tarif)

    def find_active_by_itineraire(self, id_itineraire: int, id_cooperative: int | None = None) -> Tarif | None:
        today = date.today()
        query = select(Tarif).where(
            Tarif.id_itineraire == id_itineraire,
            Tarif.is_active == True,
            Tarif.date_debut <= today,
            or_(Tarif.date_fin == None, Tarif.date_fin >= today)
        )
        if id_cooperative is not None:
            query = query.where(Tarif.id_cooperative == id_cooperative)
        else:
            query = query.where(Tarif.id_cooperative == None)
        return self.db.scalar(query)

    def create(self, tarif: Tarif) -> Tarif:
        self.db.add(tarif)
        self.db.commit()
        self.db.refresh(tarif)
        return tarif

    def update(self, tarif: Tarif) -> Tarif:
        self.db.commit()
        self.db.refresh(tarif)
        return tarif

    def delete(self, tarif: Tarif) -> None:
        self.db.delete(tarif)
        self.db.commit()
