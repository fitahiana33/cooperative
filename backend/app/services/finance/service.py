from datetime import date, datetime, timezone
from decimal import Decimal
from math import ceil
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.billet import BilletStatus
from app.models.finance import Caisse, CaisseStatus, OperationCaisse, OperationType, Paiement, PaiementMethode, PaiementStatus
from app.models.gare import Gare
from app.models.cooperative import GareCooperative
from app.models.place import DepartPlaceStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.depart import Depart
from app.services.notification import NotificationService


class FinanceService:
    def __init__(self, db: Session):
        self.db = db

    def _summary(self, caisse: Caisse) -> dict:
        rows = self.db.execute(
            select(OperationCaisse.type_operation, func.coalesce(func.sum(OperationCaisse.montant), 0))
            .where(OperationCaisse.id_caisse == caisse.id)
            .group_by(OperationCaisse.type_operation)
        ).all()
        values = {getattr(key, "value", str(key)): Decimal(value) for key, value in rows}
        recettes = values.get(OperationType.RECETTE.value, Decimal("0"))
        depenses = values.get(OperationType.DEPENSE.value, Decimal("0"))
        commissions = values.get(OperationType.COMMISSION.value, Decimal("0"))
        return {
            "total_recettes": recettes,
            "total_depenses": depenses,
            "total_commissions": commissions,
            "solde": Decimal(caisse.montant_ouverture) + recettes - depenses - commissions,
        }

    def _caisse_read(self, caisse: Caisse) -> dict:
        values = {attribute.key: getattr(caisse, attribute.key) for attribute in Caisse.__mapper__.column_attrs}
        return {**values, **self._summary(caisse)}

    def _get_caisse(self, caisse_id: int, gare_ids: set[int] | None = None) -> Caisse:
        item = self.db.get(Caisse, caisse_id)
        if not item or (gare_ids is not None and item.id_gare not in gare_ids):
            raise HTTPException(404, "Caisse introuvable.")
        return item

    def get_caisse(self, caisse_id: int, *, gare_ids: set[int] | None = None) -> dict:
        item = self._get_caisse(caisse_id, gare_ids)
        return self._caisse_read(item)

    def list_operations(self, caisse_id: int, *, page: int = 1, page_size: int = 100, gare_ids: set[int] | None = None):
        caisse = self._get_caisse(caisse_id, gare_ids)
        statement = select(OperationCaisse).where(OperationCaisse.id_caisse == caisse_id)
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(self.db.scalars(statement.order_by(OperationCaisse.date_operation.desc(), OperationCaisse.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def list_caisses(self, *, page: int = 1, page_size: int = 20, id_gare: int | None = None, gare_ids: set[int] | None = None):
        statement = select(Caisse)
        if id_gare:
            statement = statement.where(Caisse.id_gare == id_gare)
        if gare_ids is not None:
            statement = statement.where(Caisse.id_gare.in_(gare_ids))
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(self.db.scalars(statement.order_by(Caisse.date_ouverture.desc(), Caisse.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return {"items": [self._caisse_read(item) for item in items], "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def open_caisse(self, *, gare_id: int, agent_id: int, montant_ouverture: Decimal) -> dict:
        gare = self.db.get(Gare, gare_id)
        if not gare or not gare.is_active:
            raise HTTPException(422, "La gare doit être active.")
        if self.db.scalar(select(Caisse).where(Caisse.id_gare == gare_id, Caisse.statut == CaisseStatus.OUVERTE)):
            raise HTTPException(409, "Une caisse est déjà ouverte pour cette gare.")
        item = Caisse(id_gare=gare_id, id_agent=agent_id, montant_ouverture=montant_ouverture, statut=CaisseStatus.OUVERTE)
        self.db.add(item)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Une caisse est déjà ouverte pour cette gare.")
        self.db.refresh(item)
        return self._caisse_read(item)

    def close_caisse(self, caisse_id: int, *, montant_cloture: Decimal | None = None, gare_ids: set[int] | None = None) -> dict:
        item = self._get_caisse(caisse_id, gare_ids)
        if item.statut != CaisseStatus.OUVERTE:
            raise HTTPException(409, "Cette caisse est déjà clôturée.")
        expected = self._summary(item)["solde"]
        if montant_cloture is not None and montant_cloture != expected:
            raise HTTPException(422, f"Le montant de clôture attendu est {expected}.")
        item.montant_cloture = expected if montant_cloture is None else montant_cloture
        item.date_cloture = datetime.now(timezone.utc)
        item.statut = CaisseStatus.CLOTUREE
        self.db.commit()
        self.db.refresh(item)
        return self._caisse_read(item)

    def add_operation(self, caisse_id: int, *, type_operation: str, montant: Decimal, id_cooperative: int | None = None, description: str | None = None, gare_ids: set[int] | None = None) -> OperationCaisse:
        caisse = self._get_caisse(caisse_id, gare_ids)
        if caisse.statut != CaisseStatus.OUVERTE:
            raise HTTPException(422, "La caisse doit être ouverte.")
        if type_operation not in {OperationType.DEPENSE, OperationType.COMMISSION}:
            raise HTTPException(422, "Les recettes sont générées à partir d'un paiement validé.")
        if id_cooperative is not None and not self.db.get(Cooperative, id_cooperative):
            raise HTTPException(404, "Coopérative introuvable.")
        if id_cooperative is not None:
            cooperative = self.db.get(Cooperative, id_cooperative)
            if not cooperative.is_active:
                raise HTTPException(422, "La cooperative doit etre active.")
            linked = self.db.scalar(
                select(GareCooperative.id_gare).where(
                    GareCooperative.id_gare == caisse.id_gare,
                    GareCooperative.id_cooperative == id_cooperative,
                    GareCooperative.is_active.is_(True),
                    (GareCooperative.date_debut.is_(None) | (GareCooperative.date_debut <= date.today())),
                    (GareCooperative.date_fin.is_(None) | (GareCooperative.date_fin >= date.today())),
                )
            )
            if linked is None:
                raise HTTPException(422, "La cooperative n'est pas autorisee sur la gare de cette caisse.")
        item = OperationCaisse(id_caisse=caisse_id, type_operation=type_operation, montant=montant, id_cooperative=id_cooperative, description=description)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_payments(self, *, page: int = 1, page_size: int = 20, reservation_id: int | None = None, cooperative_ids: set[int] | None = None):
        statement = select(Paiement).join(Reservation).join(Depart, Depart.id == Reservation.id_depart)
        if reservation_id:
            statement = statement.where(Paiement.id_reservation == reservation_id)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(self.db.scalars(statement.order_by(Paiement.date_paiement.desc(), Paiement.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def _ensure_depart_station(self, caisse: Caisse, depart: Depart) -> None:
        if depart is None:
            return
        linked = self.db.scalar(
            select(GareCooperative.id_gare).where(
                GareCooperative.id_gare == caisse.id_gare,
                GareCooperative.id_cooperative == depart.id_cooperative,
                GareCooperative.is_active.is_(True),
                (GareCooperative.date_debut.is_(None) | (GareCooperative.date_debut <= depart.date_depart)),
                (GareCooperative.date_fin.is_(None) | (GareCooperative.date_fin >= depart.date_depart)),
            )
        )
        if linked is None:
            raise HTTPException(422, "La caisse ne correspond pas à une gare autorisée pour le départ.")

    def create_cash_payment(self, *, reservation_id: int, caisse_id: int, amount: Decimal, reference: str | None, agent_id: int, gare_ids: set[int] | None = None) -> Paiement:
        reservation = self.db.get(Reservation, reservation_id)
        if not reservation:
            raise HTTPException(404, "Réservation introuvable.")
        caisse = self._get_caisse(caisse_id, gare_ids)
        if caisse.statut != CaisseStatus.OUVERTE:
            raise HTTPException(422, "La caisse doit être ouverte pour encaisser un paiement.")
        self._ensure_depart_station(caisse, getattr(reservation, "depart", None))
        if reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être payée.")
        already_paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(Paiement.id_reservation == reservation_id, Paiement.statut == PaiementStatus.VALIDE)) or Decimal("0")
        remaining = Decimal(reservation.montant_total) - Decimal(already_paid)
        if amount != remaining:
            raise HTTPException(422, f"Le montant à payer est exactement {remaining} {getattr(reservation.depart.tarif, 'devise', '')}.")
        item = Paiement(id_reservation=reservation_id, montant=amount, methode=PaiementMethode.ESPECES, reference_paiement=reference or f"CASH-{uuid4().hex[:12].upper()}", statut=PaiementStatus.VALIDE, id_agent=agent_id)
        self.db.add(item)
        self.db.flush()
        reservation.statut = ReservationStatus.PAYEE
        self.db.add(OperationCaisse(id_caisse=caisse_id, type_operation=OperationType.RECETTE, montant=amount, id_paiement=item.id, id_cooperative=reservation.depart.id_cooperative, description=f"Paiement {item.reference_paiement}"))
        NotificationService.add(self.db, user_id=reservation.id_user, type_notification="CONFIRMATION_PAIEMENT", titre="Paiement confirmé", message=f"Le paiement de la réservation {reservation.numero_reservation} est confirmé.", reservation_id=reservation.id, depart_id=reservation.id_depart)
        self.db.commit()
        self.db.refresh(item)
        return item

    def refund(self, payment_id: int, *, caisse_id: int, agent_id: int, gare_ids: set[int] | None = None, commit: bool = True) -> Paiement:
        item = self.db.get(Paiement, payment_id)
        if not item:
            raise HTTPException(404, "Paiement introuvable.")
        if item.statut != PaiementStatus.VALIDE:
            raise HTTPException(409, "Seul un paiement validé peut être remboursé.")
        caisse = self._get_caisse(caisse_id, gare_ids)
        if caisse.statut != CaisseStatus.OUVERTE:
            raise HTTPException(422, "La caisse doit être ouverte pour enregistrer un remboursement.")
        reservation = item.reservation
        if not reservation:
            raise HTTPException(409, "La réservation associée est introuvable.")
        self._ensure_depart_station(caisse, getattr(reservation, "depart", None))
        if reservation.statut in {ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Une réservation déjà embarquée ou terminée ne peut plus être remboursée.")
        item.statut = PaiementStatus.REMBOURSE
        self.db.add(OperationCaisse(id_caisse=caisse_id, type_operation=OperationType.DEPENSE, montant=item.montant, id_paiement=item.id, description=f"Remboursement {item.reference_paiement or item.id}"))
        reservation.statut = ReservationStatus.ANNULEE
        for reservation_place in reservation.places:
            if reservation_place.depart_place and reservation_place.depart_place.statut == DepartPlaceStatus.RESERVEE:
                reservation_place.depart_place.statut = DepartPlaceStatus.DISPONIBLE
            if reservation_place.billet and reservation_place.billet.statut == BilletStatus.VALIDE:
                reservation_place.billet.statut = BilletStatus.ANNULE
        NotificationService.add(self.db, user_id=reservation.id_user, type_notification="ANNULATION", titre="Paiement remboursé", message=f"Le paiement de la réservation {reservation.numero_reservation} a été remboursé.", reservation_id=reservation.id, depart_id=reservation.id_depart)
        if commit:
            self.db.commit()
            self.db.refresh(item)
        return item
