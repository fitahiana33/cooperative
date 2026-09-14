from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.depart import Depart


class DepartRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, depart_id: int) -> Depart | None:
        return self.db.get(Depart, depart_id)

    def find_by_date_vehicule(self, date_depart: date, id_vehicule: int) -> Depart | None:
        return self.db.scalar(
            select(Depart).where(
                Depart.date_depart == date_depart,
                Depart.id_vehicule == id_vehicule
            )
        )

    def create(self, depart: Depart) -> Depart:
        self.db.add(depart)
        self.db.commit()
        self.db.refresh(depart)
        return depart

    def update(self, depart: Depart) -> Depart:
        self.db.commit()
        self.db.refresh(depart)
        return depart

    def delete(self, depart: Depart) -> None:
        self.db.delete(depart)
        self.db.commit()
