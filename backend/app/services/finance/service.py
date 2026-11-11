from datetime import date, datetime, timedelta, timezone
import hashlib
import hmac
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from math import ceil
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.billet import BilletStatus
from app.models.finance import Caisse, CaisseStatus, OperationCaisse, OperationType, Paiement, PaiementMethode, PaiementStatus
from app.models.gare import Gare
from app.models.cooperative import GareCooperative
from app.models.place import DepartPlaceStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.depart import Depart, DepartStatus
from app.services.billet import BilletService
from app.services.notification import NotificationService
from app.services.audit import AuditService
from app.services.booking_policy import minimum_deposit
from app.core.clock import local_today
from app.core.config import settings


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

    def _caisse_read(self, caisse: Caisse, summary: dict | None = None) -> dict:
        values = {attribute.key: getattr(caisse, attribute.key) for attribute in Caisse.__mapper__.column_attrs}
        return {**values, **(summary if summary is not None else self._summary(caisse))}

    def _get_caisse(self, caisse_id: int, gare_ids: set[int] | None = None, *, lock: bool = False) -> Caisse:
        item = self.db.get(Caisse, caisse_id, with_for_update=True, populate_existing=True) if lock else self.db.get(Caisse, caisse_id)
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

    def list_caisses(self, *, page: int = 1, page_size: int = 20, id_gare: int | None = None, gare_ids: set[int] | None = None, sort_by: str = "date_ouverture", sort_order: str = "desc"):
        statement = select(Caisse)
        if id_gare:
            statement = statement.where(Caisse.id_gare == id_gare)
        if gare_ids is not None:
            statement = statement.where(Caisse.id_gare.in_(gare_ids))
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        sort_column = {"date_ouverture": Caisse.date_ouverture, "statut": Caisse.statut, "montant_ouverture": Caisse.montant_ouverture}.get(sort_by, Caisse.date_ouverture)
        order = sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()
        items = list(self.db.scalars(statement.order_by(order, Caisse.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        totals = {}
        if items:
            rows = self.db.execute(select(OperationCaisse.id_caisse, OperationCaisse.type_operation,
                func.sum(OperationCaisse.montant)).where(OperationCaisse.id_caisse.in_([item.id for item in items]))
                .group_by(OperationCaisse.id_caisse, OperationCaisse.type_operation))
            for caisse_id, kind, amount in rows:
                totals.setdefault(caisse_id, {})[str(kind)] = Decimal(amount)
        summaries = {}
        for item in items:
            values = totals.get(item.id, {})
            receipts, expenses, commissions = (values.get(key, Decimal("0")) for key in ("RECETTE", "DEPENSE", "COMMISSION"))
            summaries[item.id] = {"total_recettes": receipts, "total_depenses": expenses, "total_commissions": commissions,
                                  "solde": Decimal(item.montant_ouverture) + receipts - expenses - commissions}
        return {"items": [self._caisse_read(item, summaries[item.id]) for item in items], "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def open_caisse(self, *, gare_id: int, agent_id: int, montant_ouverture: Decimal) -> dict:
        gare = self.db.get(Gare, gare_id)
        if not gare or not gare.is_active:
            raise HTTPException(422, "La gare doit être active.")
        if self.db.scalar(select(Caisse).where(Caisse.id_gare == gare_id, Caisse.statut == CaisseStatus.OUVERTE)):
            raise HTTPException(409, "Une caisse est déjà ouverte pour cette gare.")
        item = Caisse(id_gare=gare_id, id_agent=agent_id, montant_ouverture=montant_ouverture, statut=CaisseStatus.OUVERTE)
        self.db.add(item)
        try:
            self.db.flush()
            AuditService(self.db).record(user_id=agent_id, action="CAISSE_OUVERTE", entity_type="caisse", entity_id=item.id,
                after={"montant_ouverture": montant_ouverture})
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Une caisse est déjà ouverte pour cette gare.")
        self.db.refresh(item)
        return self._caisse_read(item)

    def close_caisse(self, caisse_id: int, *, montant_cloture: Decimal | None = None, gare_ids: set[int] | None = None, user_id: int | None = None, is_manager: bool = False) -> dict:
        item = self._get_caisse(caisse_id, gare_ids, lock=True)
        if item.statut != CaisseStatus.OUVERTE:
            raise HTTPException(409, "Cette caisse est déjà clôturée.")
        if user_id is not None and not is_manager and item.id_agent != user_id:
            raise HTTPException(403, "Seul l'agent qui a ouvert la caisse, ou un responsable, peut la clôturer.")
        expected = self._summary(item)["solde"]
        # The counted cash is recorded as is; any difference is kept as a discrepancy.
        counted = expected if montant_cloture is None else montant_cloture
        item.montant_cloture = counted
        item.ecart_cloture = counted - expected
        item.date_cloture = datetime.now(timezone.utc)
        item.statut = CaisseStatus.CLOTUREE
        AuditService(self.db).record(user_id=user_id, action="CAISSE_CLOTUREE", entity_type="caisse", entity_id=item.id, after={"compte": counted, "attendu": expected, "ecart": counted - expected})
        self.db.commit()
        self.db.refresh(item)
        return self._caisse_read(item)

    def add_operation(self, caisse_id: int, *, type_operation: str, montant: Decimal, id_cooperative: int | None = None, description: str | None = None, gare_ids: set[int] | None = None, agent_id: int | None = None) -> OperationCaisse:
        caisse = self._get_caisse(caisse_id, gare_ids, lock=True)
        if caisse.statut != CaisseStatus.OUVERTE:
            raise HTTPException(422, "La caisse doit être ouverte.")
        if type_operation not in {OperationType.DEPENSE, OperationType.COMMISSION}:
            raise HTTPException(422, "Les recettes sont générées à partir d'un paiement validé.")
        if montant > self._summary(caisse)["solde"]:
            raise HTTPException(409, "Le solde de la caisse est insuffisant pour cette sortie d'espèces.")
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
                    (GareCooperative.date_debut.is_(None) | (GareCooperative.date_debut <= local_today())),
                    (GareCooperative.date_fin.is_(None) | (GareCooperative.date_fin >= local_today())),
                )
            )
            if linked is None:
                raise HTTPException(422, "La cooperative n'est pas autorisee sur la gare de cette caisse.")
        item = OperationCaisse(id_caisse=caisse_id, id_agent=agent_id, type_operation=type_operation, montant=montant, id_cooperative=id_cooperative, description=description)
        self.db.add(item)
        self.db.flush()
        AuditService(self.db).record(user_id=agent_id, action="CAISSE_SORTIE", entity_type="caisse", entity_id=caisse_id,
            after={"operation": item.id, "type": type_operation, "montant": montant, "description": description})
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_payments(self, *, page: int = 1, page_size: int = 20, reservation_id: int | None = None, cooperative_ids: set[int] | None = None, gare_ids: set[int] | None = None, to_verify: bool = False, to_refund: bool = False, search: str | None = None, sort_by: str = "date_paiement", sort_order: str = "desc"):
        statement = select(Paiement, Reservation.numero_reservation).join(Reservation).join(Depart, Depart.id == Reservation.id_depart)
        if gare_ids is not None:
            statement = statement.where(Depart.id_gare.in_(gare_ids))
        if reservation_id:
            statement = statement.where(Paiement.id_reservation == reservation_id)
        if to_verify:
            statement = statement.where(Paiement.statut == PaiementStatus.EN_ATTENTE, Paiement.verification_requise.is_(True))
        if to_refund:
            statement = statement.where(Paiement.statut == PaiementStatus.VALIDE, Paiement.remboursement_demande_le.is_not(None))
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(or_(Paiement.reference_paiement.ilike(term), Reservation.numero_reservation.ilike(term)))
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        sort_column = {"date_paiement": Paiement.date_paiement, "statut": Paiement.statut, "montant": Paiement.montant}.get(sort_by, Paiement.date_paiement)
        order = sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()
        rows = list(self.db.execute(statement.order_by(order, Paiement.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        items = [{**{attribute.key: getattr(row.Paiement, attribute.key) for attribute in Paiement.__mapper__.column_attrs}, "numero_reservation": row.numero_reservation} for row in rows]
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def _ensure_depart_station(self, caisse: Caisse, depart: Depart) -> None:
        if depart is None:
            return
        if depart.id_gare is not None and depart.id_gare != caisse.id_gare:
            raise HTTPException(422, "La caisse doit appartenir à la gare d'origine du départ.")
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

    def create_cash_payment(self, *, reservation_id: int, caisse_id: int, amount: Decimal, reference: str | None, agent_id: int, gare_ids: set[int] | None = None, commit: bool = True) -> Paiement:
        # Lock the reservation so two simultaneous payments cannot both pass the checks.
        reservation = self.db.scalar(select(Reservation).where(Reservation.id == reservation_id).with_for_update())
        if not reservation:
            raise HTTPException(404, "Réservation introuvable.")
        caisse = self._get_caisse(caisse_id, gare_ids, lock=True)
        if caisse.statut != CaisseStatus.OUVERTE:
            raise HTTPException(422, "La caisse doit être ouverte pour encaisser un paiement.")
        self._ensure_depart_station(caisse, getattr(reservation, "depart", None))
        if reservation.statut == ReservationStatus.EN_ATTENTE and reservation.date_expiration and reservation.date_expiration <= datetime.now(timezone.utc):
            # The trigger on reservations releases the seats.
            reservation.statut = ReservationStatus.EXPIREE
            self.db.commit()
            raise HTTPException(409, "Le délai de paiement de cette réservation est dépassé ; les places ont été libérées.")
        if reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être payée.")
        if reservation.depart.statut in {DepartStatus.PARTI, DepartStatus.TERMINE, DepartStatus.ANNULE}:
            raise HTTPException(409, "Ce départ n'accepte plus de paiement de réservation.")
        already_paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(Paiement.id_reservation == reservation_id, Paiement.statut == PaiementStatus.VALIDE)) or Decimal("0")
        remaining = Decimal(reservation.montant_total) - Decimal(already_paid)
        if remaining <= 0:
            raise HTTPException(409, "Cette réservation est déjà intégralement payée.")
        if amount != remaining:
            raise HTTPException(422, f"Le montant à payer est exactement {remaining} {getattr(reservation.depart.tarif, 'devise', '')}.")
        item = Paiement(id_reservation=reservation_id, montant=amount, methode=PaiementMethode.ESPECES, reference_paiement=reference or f"CASH-{uuid4().hex[:12].upper()}", statut=PaiementStatus.VALIDE, date_validation=datetime.now(timezone.utc), id_agent=agent_id)
        self.db.add(item)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Cette réservation est déjà payée.")
        reservation.statut = ReservationStatus.PAYEE
        # A reservation paid without prior confirmation still needs its tickets.
        BilletService.issue_for_reservation(self.db, reservation)
        self.db.add(OperationCaisse(id_caisse=caisse_id, id_agent=agent_id, type_operation=OperationType.RECETTE, montant=amount, id_paiement=item.id, id_cooperative=reservation.depart.id_cooperative, description=f"Paiement {item.reference_paiement}"))
        commission_rate = Decimal(str(settings.default_commission_rate)) / Decimal("100")
        if commission_rate > 0:
            commission = (amount * commission_rate).quantize(Decimal("0.01"))
            if commission > 0:
                self.db.add(OperationCaisse(
                    id_caisse=caisse_id,
                    id_agent=agent_id,
                    type_operation=OperationType.COMMISSION,
                    montant=commission,
                    id_paiement=item.id,
                    id_cooperative=reservation.depart.id_cooperative,
                    description=f"Commission ({settings.default_commission_rate:g} %) {item.reference_paiement}",
                ))
        AuditService(self.db).record(user_id=agent_id, action="PAIEMENT_ESPECES_VALIDE", entity_type="paiement", entity_id=item.id, after={"montant": amount, "caisse": caisse_id})
        NotificationService.add(self.db, user_id=reservation.id_user, type_notification="CONFIRMATION_PAIEMENT", titre="Paiement confirmé", message=f"Le paiement de la réservation {reservation.numero_reservation} est confirmé.", reservation_id=reservation.id, depart_id=reservation.id_depart)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(item)
        return item

    @staticmethod
    def _minimum_deposit(total: Decimal, reservation: Reservation | None = None) -> Decimal:
        return minimum_deposit(total, rate=reservation.taux_acompte if reservation else None,
                               floor=reservation.plancher_acompte if reservation else None)

    def pending_online_payment(self, reservation_id: int, *, user_id: int | None = None):
        reservation = self.db.get(Reservation, reservation_id)
        if not reservation or (user_id is not None and reservation.id_user != user_id):
            raise HTTPException(404, "Réservation introuvable.")
        item = self.db.scalar(select(Paiement).where(Paiement.id_reservation == reservation_id,
            Paiement.statut == PaiementStatus.EN_ATTENTE, Paiement.fournisseur == "papi").order_by(Paiement.id.desc()).limit(1))
        return self._online_read(item) if item else None

    def create_online_payment(self, *, reservation_id: int, amount: Decimal, idempotency_key: str, user_id: int, provider: str = "MVOLA", payer_phone: str | None = None) -> dict:
        return self.create_papi_payment(
            reservation_id=reservation_id,
            amount=amount,
            idempotency_key=idempotency_key,
            user_id=user_id,
            client_name=None,
            payer_phone=payer_phone,
            payer_email=None,
            provider=provider,
        )

    def create_papi_payment(
        self,
        *,
        reservation_id: int,
        amount: Decimal,
        idempotency_key: str,
        user_id: int | None,
        client_name: str | None,
        payer_phone: str | None,
        payer_email: str | None,
        provider: str,
    ) -> dict:
        """Create a Papi payment link; the callback is the only source of truth."""
        if not settings.online_payment_enabled:
            raise HTTPException(503, "Le paiement mobile money est désactivé pour le moment.")
        if settings.payment_provider.lower() != "papi":
            raise HTTPException(503, "Le fournisseur Papi n'est pas activé.")
        reservation = self.db.scalar(select(Reservation).where(Reservation.id == reservation_id).with_for_update())
        if not reservation:
            raise HTTPException(404, "Réservation introuvable.")
        if user_id is not None and reservation.id_user != user_id:
            raise HTTPException(403, "Cette réservation n'appartient pas à votre compte.")
        existing = self.db.scalar(select(Paiement).where(Paiement.cle_idempotence == idempotency_key))
        if existing:
            if existing.id_reservation != reservation_id or Decimal(existing.montant) != Decimal(amount):
                raise HTTPException(409, "Cette clé de paiement est déjà utilisée pour une autre demande.")
        if reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être payée.")
        if reservation.statut == ReservationStatus.EN_ATTENTE and reservation.date_expiration and reservation.date_expiration <= datetime.now(timezone.utc):
            reservation.statut = ReservationStatus.EXPIREE
            self.db.commit()
            raise HTTPException(409, "Cette réservation a expiré ; ses places ont été libérées.")
        if reservation.depart.statut in {DepartStatus.PARTI, DepartStatus.TERMINE, DepartStatus.ANNULE}:
            raise HTTPException(409, "Ce départ n'accepte plus de paiement de réservation.")
        from app.services.booking_policy import booking_policy
        from app.services.depart.status import booking_is_open, mark_overdue_departures

        mark_overdue_departures(self.db, commit=False)
        close_minutes = int(booking_policy(self.db)["booking_close_minutes"])
        if not booking_is_open(reservation.depart, close_minutes):
            raise HTTPException(
                409,
                "Le délai de réservation est terminé ; ce paiement ne peut plus être initié.",
            )
        if existing:
            return self._online_read(existing)
        other_payment = self.db.scalar(select(Paiement).where(
            Paiement.id_reservation == reservation_id,
            Paiement.statut == PaiementStatus.EN_ATTENTE,
            Paiement.id != existing.id if existing else True,
        ).limit(1))
        if other_payment is not None:
            if Decimal(other_payment.montant) == Decimal(amount) and other_payment.fournisseur == "papi":
                return self._online_read(other_payment)
            raise HTTPException(409, "Un paiement existe déjà pour cette réservation. Consultez son statut ou réglez le solde au guichet.")
        total = Decimal(reservation.montant_total)
        amount = Decimal(amount)
        paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(
            Paiement.id_reservation == reservation_id, Paiement.statut == PaiementStatus.VALIDE,
            Paiement.remboursement_demande_le.is_(None))) or Decimal("0")
        remaining = max(Decimal("0"), total - Decimal(paid))
        minimum = remaining if paid else self._minimum_deposit(total, reservation)
        if remaining <= 0:
            raise HTTPException(409, "Cette réservation est déjà entièrement réglée.")
        if amount != amount.to_integral_value():
            raise HTTPException(422, "Le montant doit être un nombre entier d'ariary.")
        if amount < minimum:
            raise HTTPException(422, f"L'avance minimale est de {minimum} Ar.")
        if amount > remaining:
            raise HTTPException(422, f"L'avance ne peut pas dépasser le total de {total} Ar.")
        if provider not in {"MVOLA", "ORANGE_MONEY", "AIRTEL_MONEY"}:
            raise HTTPException(422, "Le moyen de paiement mobile money est invalide.")
        reference = f"PAY-{uuid4().hex.upper()}"
        item = existing or Paiement(
            id_reservation=reservation_id, montant=amount, methode=PaiementMethode.MOBILE_MONEY,
            reference_paiement=reference, fournisseur="papi", cle_idempotence=idempotency_key,
            statut=PaiementStatus.EN_ATTENTE, id_agent=None, verification_requise=True,
        )
        if existing and Decimal(existing.montant) != amount:
            raise HTTPException(409, "Cette demande de paiement existe déjà avec un autre montant.")
        self.db.add(item)
        if reservation.statut == ReservationStatus.EN_ATTENTE:
            link_deadline = datetime.now(timezone.utc) + timedelta(hours=settings.papi_valid_duration_hours)
            reservation.date_expiration = max(reservation.date_expiration or link_deadline, link_deadline)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            item = self.db.scalar(select(Paiement).where(Paiement.cle_idempotence == idempotency_key))
            if item and item.id_reservation == reservation_id and Decimal(item.montant) == amount:
                return self._online_read(item)
            raise HTTPException(409, "Cette demande de paiement existe déjà.")
        self.db.refresh(item)
        try:
            papi_data = self._create_papi_link(
                amount=amount,
                reference=reference,
                description=f"Avance réservation {reservation.numero_reservation}",
                client_name=client_name or reservation.nom_reservataire or "Passager",
                payer_phone=payer_phone or reservation.telephone_reservataire,
                payer_email=payer_email or reservation.email_reservataire,
                provider=provider,
            )
        except HTTPException:
            # A timeout is an unknown remote outcome, never proof of failure.
            # Keep the merchant reference for reconciliation and signed callbacks.
            item.verification_requise = True
            self.db.commit()
            return self._online_read(item)
        item.verification_requise = False
        item.checkout_url = papi_data["paymentLink"]
        item.notification_token = papi_data.get("notificationToken")
        item.reference_fournisseur = papi_data.get("paymentReference")
        # Keep the seats for the entire configured validity of the link.
        # Otherwise a link valid for one hour could outlive a 30-minute hold.
        if reservation.statut == ReservationStatus.EN_ATTENTE:
            link_deadline = datetime.now(timezone.utc) + timedelta(hours=settings.papi_valid_duration_hours)
            reservation.date_expiration = max(reservation.date_expiration or link_deadline, link_deadline)
        self.db.commit()
        AuditService(self.db).record(user_id=user_id, action="PAIEMENT_EN_LIGNE_INITIE", entity_type="paiement", entity_id=item.id, after={"statut": item.statut, "fournisseur": item.fournisseur})
        self.db.commit()
        return self._online_read(item)

    @staticmethod
    def _create_papi_link(*, amount: Decimal, reference: str, description: str, client_name: str, payer_phone: str | None, payer_email: str | None, provider: str) -> dict:
        from app.integrations.papi import create_payment_link
        return create_payment_link(amount=amount, reference=reference, description=description, client_name=client_name,
            payer_phone=payer_phone, payer_email=payer_email, provider=provider)

    def _online_read(self, item: Paiement) -> dict:
        paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(Paiement.id_reservation == item.id_reservation, Paiement.statut == PaiementStatus.VALIDE)) or Decimal("0")
        total = Decimal(item.reservation.montant_total) if item.reservation else Decimal(item.montant)
        return {
            "id_paiement": item.id, "statut": item.statut, "fournisseur": item.fournisseur or settings.payment_provider,
            "reference_paiement": item.reference_paiement or "", "montant": item.montant,
            "verification_requise": item.verification_requise,
            "message": ("Demande à vérifier auprès du prestataire ; ne renouvelez pas le paiement." if item.verification_requise else
                        "Paiement en attente de confirmation de Papi." if item.statut == PaiementStatus.EN_ATTENTE else
                        "Cette tentative a échoué. Vous pouvez préparer une nouvelle demande." if item.statut == PaiementStatus.ECHOUE else "Paiement traité."),
            "checkout_url": item.checkout_url if item.statut == PaiementStatus.EN_ATTENTE else None,
            "acompte_minimum": self._minimum_deposit(total, item.reservation),
            "montant_restant": max(Decimal("0"), total - Decimal(paid)),
        }

    def handle_online_webhook(self, *, provider: str, payload: dict, signature: str | None, raw_body: bytes) -> dict:
        if not isinstance(payload, dict):
            raise HTTPException(422, "La notification de paiement doit être un objet JSON.")
        if not settings.online_payment_enabled:
            raise HTTPException(503, "Les paiements en ligne sont désactivés.")
        if provider.lower() != "papi" or settings.payment_provider.lower() != "papi":
            raise HTTPException(404, "Fournisseur de paiement inconnu.")
        if not self._verify_papi_signature(raw_body, signature):
            raise HTTPException(401, "Signature de webhook invalide.")
        raw = str(payload.get("merchantPaymentReference") or "")
        token = str(payload.get("notificationToken") or "")
        status_value = str(payload.get("paymentStatus") or "").upper()
        if not raw or not token or status_value not in {"SUCCESS", "FAILED", "PENDING"}:
            raise HTTPException(422, "Webhook Papi incomplet.")
        payment_id = self.db.scalar(select(Paiement.id).where(Paiement.reference_paiement == raw, Paiement.fournisseur == "papi"))
        item = self.db.get(Paiement, payment_id) if payment_id is not None else None
        if not item:
            raise HTTPException(404, "Paiement fournisseur introuvable.")
        # Serialize callback, cancellation, refund and cash settlement in the
        # same order: reservation first, payment second.
        reservation = self.db.scalar(select(Reservation).where(Reservation.id == item.id_reservation).with_for_update().execution_options(populate_existing=True))
        item = self.db.get(Paiement, item.id, with_for_update=True, populate_existing=True)
        if item.notification_token and not hmac.compare_digest(item.notification_token, token):
            raise HTTPException(401, "Token de notification Papi invalide.")
        if not item.notification_token:
            # A correctly signed callback can recover a lost link-creation response.
            item.notification_token = token
        try:
            received_amount = Decimal(str(payload.get("amount", "0")))
        except InvalidOperation:
            raise HTTPException(422, "Le montant du webhook Papi est invalide.")
        if not received_amount.is_finite() or received_amount != Decimal(item.montant):
            raise HTTPException(422, "Le montant du webhook Papi ne correspond pas à la réservation.")
        if item.statut in {PaiementStatus.VALIDE, PaiementStatus.REMBOURSE}:
            return {"id_paiement": item.id, "statut": item.statut, "idempotent": True}
        if status_value == "PENDING":
            return {"id_paiement": item.id, "statut": item.statut, "idempotent": True}
        if status_value == "SUCCESS":
            now = datetime.now(timezone.utc)
            item.date_validation = now
            item.date_paiement = now
            expired_hold = reservation.statut == ReservationStatus.EN_ATTENTE and reservation.date_expiration and reservation.date_expiration <= now
            closed = reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE} or reservation.depart.statut in {DepartStatus.PARTI, DepartStatus.TERMINE, DepartStatus.ANNULE}
            if expired_hold:
                reservation.statut = ReservationStatus.EXPIREE
                closed = True
            # Persist expiry before the payment trigger can mark it paid.
            if closed:
                # Flush the reservation independently of the incoming payment.
                self.db.flush([reservation])
                item.statut = PaiementStatus.VALIDE
                self.request_refund(item)
            else:
                paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(
                    Paiement.id_reservation == reservation.id, Paiement.id != item.id, Paiement.statut == PaiementStatus.VALIDE,
                )) or Decimal("0")
                item.statut = PaiementStatus.VALIDE
                if Decimal(paid) + Decimal(item.montant) > Decimal(reservation.montant_total):
                    self.request_refund(item)
                else:
                    reservation.statut = ReservationStatus.PAYEE
                    BilletService.issue_for_reservation(self.db, reservation)
            if not closed and item.remboursement_demande_le is None and reservation.id_user:
                NotificationService.add(self.db, user_id=reservation.id_user, type_notification="CONFIRMATION_PAIEMENT", titre="Paiement en ligne confirmé", message=f"Le paiement de la réservation {reservation.numero_reservation} est confirmé.", reservation_id=reservation.id, depart_id=reservation.id_depart)
        else:
            item.statut = PaiementStatus.ECHOUE
        item.verification_requise = False
        item.webhook_recu_le = datetime.now(timezone.utc)
        item.reference_fournisseur = str(payload.get("paymentReference") or item.reference_fournisseur or raw)[:150]
        AuditService(self.db).record(user_id=None, action="PAIEMENT_WEBHOOK", entity_type="paiement", entity_id=item.id,
            after={"statut": item.statut, "montant": item.montant, "reference_fournisseur": item.reference_fournisseur})
        self.db.commit()
        return {"id_paiement": item.id, "statut": item.statut, "idempotent": False}

    @staticmethod
    def _verify_papi_signature(raw_body: bytes, header: str | None, tolerance_seconds: int = 300) -> bool:
        if not header or not settings.papi_signing_secret:
            return False
        parts = dict(item.strip().split("=", 1) for item in header.split(",") if "=" in item)
        timestamp, received = parts.get("t", ""), parts.get("v1", "")
        if not timestamp.isdigit() or len(received) != 64:
            return False
        try:
            if abs(int(datetime.now(timezone.utc).timestamp()) - int(timestamp)) > tolerance_seconds:
                return False
        except ValueError:
            return False
        expected = hmac.new(settings.papi_signing_secret.encode("utf-8"), f"{timestamp}.".encode("ascii") + raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, received)

    def request_refund(self, payment: Paiement) -> None:
        """Mark a payment as to be refunded by a cashier (the reservation is cancelled meanwhile)."""
        if payment.statut == PaiementStatus.VALIDE and payment.remboursement_demande_le is None:
            payment.remboursement_demande_le = datetime.now(timezone.utc)

    def refund(self, payment_id: int, *, caisse_id: int | None, agent_id: int, gare_ids: set[int] | None = None, commit: bool = True, method: str = "ESPECES", refund_reference: str | None = None) -> Paiement:
        item = self.db.get(Paiement, payment_id)
        if not item:
            raise HTTPException(404, "Paiement introuvable.")
        # Same reservation lock as payment and cancellation, then payment.
        self.db.execute(select(Reservation.id).where(Reservation.id == item.id_reservation).with_for_update())
        item = self.db.get(Paiement, payment_id, with_for_update=True, populate_existing=True)
        if item.statut != PaiementStatus.VALIDE:
            raise HTTPException(409, "Seul un paiement validé peut être remboursé.")
        reservation = item.reservation
        if not reservation:
            raise HTTPException(409, "La réservation associée est introuvable.")
        self.db.refresh(reservation)
        if gare_ids is not None and reservation.depart.id_gare not in gare_ids:
            raise HTTPException(404, "Paiement introuvable.")
        if method == "ESPECES":
            if caisse_id is None:
                raise HTTPException(422, "Choisissez la caisse qui rend les espèces.")
            caisse = self._get_caisse(caisse_id, gare_ids, lock=True)
            if caisse.statut != CaisseStatus.OUVERTE:
                raise HTTPException(422, "La caisse doit être ouverte pour enregistrer un remboursement.")
            if Decimal(item.montant) > self._summary(caisse)["solde"]:
                raise HTTPException(409, "Le solde de la caisse est insuffisant pour ce remboursement.")
            self._ensure_depart_station(caisse, getattr(reservation, "depart", None))
        elif method not in {"MOBILE_MONEY", "VIREMENT", "CARTE"} or not refund_reference or len(refund_reference.strip()) < 8:
            raise HTTPException(422, "Un remboursement externe exige sa méthode et une référence de transaction vérifiable.")
        if reservation.statut in {ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Une réservation déjà embarquée ou terminée ne peut plus être remboursée.")
        if any(place.billet and place.billet.statut == BilletStatus.UTILISE for place in reservation.places):
            raise HTTPException(409, "Un passager a déjà embarqué ; ce paiement ne peut plus être remboursé.")
        already_cancelled = reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE}
        refund_only = False
        if getattr(item, "remboursement_demande_le", None) is not None and not already_cancelled:
            other_paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(
                Paiement.id_reservation == reservation.id, Paiement.id != item.id,
                Paiement.statut == PaiementStatus.VALIDE, Paiement.remboursement_demande_le.is_(None),
            )) or Decimal("0")
            refund_only = Decimal(other_paid) >= Decimal(reservation.montant_total)
        item.statut = PaiementStatus.REMBOURSE
        item.date_remboursement = datetime.now(timezone.utc)
        item.methode_remboursement = method
        item.reference_remboursement = refund_reference.strip() if refund_reference else f"CAISSE-{caisse_id}-PAY-{item.id}"
        if method == "ESPECES":
            self.db.add(OperationCaisse(id_caisse=caisse_id, id_agent=agent_id, type_operation=OperationType.DEPENSE, montant=item.montant, id_paiement=item.id, id_cooperative=getattr(getattr(reservation, "depart", None), "id_cooperative", None), description=f"Remboursement {item.reference_paiement or item.id}"))
        if not refund_only:
            reservation.statut = ReservationStatus.ANNULEE
        for reservation_place in ([] if refund_only else reservation.places):
            if not already_cancelled and reservation_place.depart_place and reservation_place.depart_place.statut == DepartPlaceStatus.RESERVEE:
                reservation_place.depart_place.statut = DepartPlaceStatus.DISPONIBLE
            if reservation_place.billet and reservation_place.billet.statut == BilletStatus.VALIDE:
                reservation_place.billet.statut = BilletStatus.ANNULE
        NotificationService.add(self.db, user_id=reservation.id_user, type_notification="ANNULATION", titre="Paiement remboursé", message=f"Le paiement de la réservation {reservation.numero_reservation} a été remboursé.", reservation_id=reservation.id, depart_id=reservation.id_depart)
        AuditService(self.db).record(user_id=agent_id, action="PAIEMENT_REMBOURSE", entity_type="paiement", entity_id=item.id, after={"montant": item.montant, "caisse": caisse_id, "reference": item.reference_remboursement, "methode": method})
        if commit:
            self.db.commit()
            self.db.refresh(item)
        return item


    def confirm_provider_failure(self, payment_id: int, *, agent_id: int, reference: str, gare_ids: set[int] | None):
        item = self.db.get(Paiement, payment_id)
        if not item:
            raise HTTPException(404, "Paiement introuvable.")
        self.db.execute(select(Reservation.id).where(Reservation.id == item.id_reservation).with_for_update())
        item = self.db.get(Paiement, payment_id, with_for_update=True, populate_existing=True)
        if gare_ids is not None and item.reservation.depart.id_gare not in gare_ids:
            raise HTTPException(404, "Paiement introuvable.")
        if item.statut != PaiementStatus.EN_ATTENTE or not item.verification_requise:
            raise HTTPException(409, "Ce paiement ne nécessite pas de vérification d’initialisation.")
        item.statut = PaiementStatus.ECHOUE
        item.verification_requise = False
        AuditService(self.db).record(user_id=agent_id, action="PAIEMENT_ECHEC_VERIFIE", entity_type="paiement", entity_id=item.id,
            after={"reference_verification": reference}, description="Absence d’encaissement vérifiée auprès du prestataire.")
        self.db.commit()
        return item
