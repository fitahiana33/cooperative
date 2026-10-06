from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.reservation import Reservation, ReservationPlace
from app.models.place import DepartPlace


class ReservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, id_reservation: int) -> Reservation | None:
        return self.db.get(Reservation, id_reservation)

    def find_by_numero(self, numero_reservation: str) -> Reservation | None:
        return self.db.scalar(select(Reservation).where(Reservation.numero_reservation == numero_reservation.strip()))

    def find_by_user(self, id_user: int) -> list[Reservation]:
        return list(self.db.scalars(select(Reservation).where(Reservation.id_user == id_user).order_by(Reservation.created_at.desc())).all())

    def find_by_depart(self, id_depart: int) -> list[Reservation]:
        return list(self.db.scalars(select(Reservation).where(Reservation.id_depart == id_depart).order_by(Reservation.created_at.desc())).all())

    def create(self, reservation: Reservation) -> Reservation:
        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)
        return reservation

    def update(self, reservation: Reservation) -> Reservation:
        self.db.commit()
        self.db.refresh(reservation)
        return reservation

    def delete(self, reservation: Reservation) -> None:
        self.db.delete(reservation)
        self.db.commit()
