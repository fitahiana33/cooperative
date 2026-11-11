"""A counter sale has one database transaction and no partial reservation."""
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.audit import AuditService
from app.services.finance import FinanceService
from app.services.reservation.service import ReservationService


def sell_at_counter(db: Session, *, user: User, depart_id: int, places: list[dict],
                    caisse_id: int | None, reference: str | None, gare_ids: set[int] | None):
    reservations = ReservationService(db)
    try:
        item = reservations.create_reservation(user=user, depart_id=depart_id, places=places, commit=False)
        item = reservations.confirm(item.id, commit=False)
        if caisse_id is not None:
            FinanceService(db).create_cash_payment(reservation_id=item.id, caisse_id=caisse_id,
                amount=item.montant_total, reference=reference, agent_id=user.id, gare_ids=gare_ids, commit=False)
        AuditService(db).record(user_id=user.id, action="VENTE_GUICHET", entity_type="reservation", entity_id=item.id,
            after={"montant": item.montant_total, "caisse": caisse_id})
        db.commit()
        return reservations._get(item.id)
    except Exception:
        db.rollback()
        raise
