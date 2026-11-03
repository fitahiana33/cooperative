from datetime import date, datetime, timezone
import hashlib
import hmac
import json
from decimal import Decimal, ROUND_CEILING
from math import ceil
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
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
from app.models.depart import Depart
from app.services.billet import BilletService
from app.services.notification import NotificationService
from app.services.audit import AuditService
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

    def close_caisse(self, caisse_id: int, *, montant_cloture: Decimal | None = None, gare_ids: set[int] | None = None, user_id: int | None = None, is_manager: bool = False) -> dict:
        item = self._get_caisse(caisse_id, gare_ids)
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
                    (GareCooperative.date_debut.is_(None) | (GareCooperative.date_debut <= local_today())),
                    (GareCooperative.date_fin.is_(None) | (GareCooperative.date_fin >= local_today())),
                )
            )
            if linked is None:
                raise HTTPException(422, "La cooperative n'est pas autorisee sur la gare de cette caisse.")
        item = OperationCaisse(id_caisse=caisse_id, type_operation=type_operation, montant=montant, id_cooperative=id_cooperative, description=description)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_payments(self, *, page: int = 1, page_size: int = 20, reservation_id: int | None = None, cooperative_ids: set[int] | None = None, to_refund: bool = False, search: str | None = None, sort_by: str = "date_paiement", sort_order: str = "desc"):
        statement = select(Paiement, Reservation.numero_reservation).join(Reservation).join(Depart, Depart.id == Reservation.id_depart)
        if reservation_id:
            statement = statement.where(Paiement.id_reservation == reservation_id)
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
        # Lock the reservation so two simultaneous payments cannot both pass the checks.
        reservation = self.db.scalar(select(Reservation).where(Reservation.id == reservation_id).with_for_update())
        if not reservation:
            raise HTTPException(404, "Réservation introuvable.")
        caisse = self._get_caisse(caisse_id, gare_ids)
        if caisse.statut != CaisseStatus.OUVERTE:
            raise HTTPException(422, "La caisse doit être ouverte pour encaisser un paiement.")
        self._ensure_depart_station(caisse, getattr(reservation, "depart", None))
        if reservation.statut == ReservationStatus.EN_ATTENTE and reservation.date_expiration and reservation.date_expiration <= datetime.now(timezone.utc):
            # The trigger on reservations releases the seats.
            reservation.statut = ReservationStatus.EXPIREE
            self.db.commit()
            raise HTTPException(409, "Le délai de paiement de cette réservation est dépassé ; les places ont été libérées.")
        if reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être payée.")
        already_paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(Paiement.id_reservation == reservation_id, Paiement.statut == PaiementStatus.VALIDE)) or Decimal("0")
        remaining = Decimal(reservation.montant_total) - Decimal(already_paid)
        if amount != remaining:
            raise HTTPException(422, f"Le montant à payer est exactement {remaining} {getattr(reservation.depart.tarif, 'devise', '')}.")
        item = Paiement(id_reservation=reservation_id, montant=amount, methode=PaiementMethode.ESPECES, reference_paiement=reference or f"CASH-{uuid4().hex[:12].upper()}", statut=PaiementStatus.VALIDE, id_agent=agent_id)
        self.db.add(item)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Cette réservation est déjà payée.")
        reservation.statut = ReservationStatus.PAYEE
        # A reservation paid without prior confirmation still needs its tickets.
        BilletService.issue_for_reservation(self.db, reservation)
        self.db.add(OperationCaisse(id_caisse=caisse_id, type_operation=OperationType.RECETTE, montant=amount, id_paiement=item.id, id_cooperative=reservation.depart.id_cooperative, description=f"Paiement {item.reference_paiement}"))
        commission_rate = Decimal(str(settings.default_commission_rate)) / Decimal("100")
        if commission_rate > 0:
            commission = (amount * commission_rate).quantize(Decimal("0.01"))
            if commission > 0:
                self.db.add(OperationCaisse(
                    id_caisse=caisse_id,
                    type_operation=OperationType.COMMISSION,
                    montant=commission,
                    id_paiement=item.id,
                    id_cooperative=reservation.depart.id_cooperative,
                    description=f"Commission ({settings.default_commission_rate:g} %) {item.reference_paiement}",
                ))
        NotificationService.add(self.db, user_id=reservation.id_user, type_notification="CONFIRMATION_PAIEMENT", titre="Paiement confirmé", message=f"Le paiement de la réservation {reservation.numero_reservation} est confirmé.", reservation_id=reservation.id, depart_id=reservation.id_depart)
        self.db.commit()
        self.db.refresh(item)
        return item

    @staticmethod
    def _minimum_deposit(total: Decimal) -> Decimal:
        return max(Decimal("300"), (Decimal(total) * Decimal("0.25")).quantize(Decimal("1"), rounding=ROUND_CEILING))

    def create_online_payment(self, *, reservation_id: int, amount: Decimal, idempotency_key: str, user_id: int) -> dict:
        return self.create_papi_payment(
            reservation_id=reservation_id,
            amount=amount,
            idempotency_key=idempotency_key,
            user_id=user_id,
            client_name=None,
            payer_phone=None,
            payer_email=None,
            provider="MVOLA",
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
        existing = self.db.scalar(select(Paiement).where(Paiement.cle_idempotence == idempotency_key))
        if existing and existing.checkout_url:
            return self._online_read(existing)
        reservation = self.db.scalar(select(Reservation).where(Reservation.id == reservation_id).with_for_update())
        if not reservation:
            raise HTTPException(404, "Réservation introuvable.")
        if user_id is not None and reservation.id_user != user_id:
            raise HTTPException(403, "Cette réservation n'appartient pas à votre compte.")
        if reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être payée.")
        total = Decimal(reservation.montant_total)
        amount = Decimal(amount)
        minimum = self._minimum_deposit(total)
        if amount != amount.to_integral_value():
            raise HTTPException(422, "Le montant doit être un nombre entier d'ariary.")
        if amount < minimum:
            raise HTTPException(422, f"L'avance minimale est de {minimum} Ar (25 % du total).")
        if amount > total:
            raise HTTPException(422, f"L'avance ne peut pas dépasser le total de {total} Ar.")
        if provider not in {"MVOLA", "ORANGE_MONEY", "AIRTEL_MONEY"}:
            raise HTTPException(422, "Le moyen de paiement mobile money est invalide.")
        reference = f"RES-{reservation.numero_reservation}-ADV"
        item = existing or Paiement(
            id_reservation=reservation_id, montant=amount, methode=PaiementMethode.MOBILE_MONEY,
            reference_paiement=reference, fournisseur="papi", cle_idempotence=idempotency_key,
            statut=PaiementStatus.EN_ATTENTE, id_agent=None,
        )
        if existing and Decimal(existing.montant) != amount:
            raise HTTPException(409, "Cette demande de paiement existe déjà avec un autre montant.")
        self.db.add(item)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            item = self.db.scalar(select(Paiement).where(Paiement.cle_idempotence == idempotency_key))
            if item:
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
            item.statut = PaiementStatus.ECHOUE
            self.db.commit()
            raise
        item.checkout_url = papi_data["paymentLink"]
        item.notification_token = papi_data.get("notificationToken")
        item.reference_fournisseur = papi_data.get("paymentReference")
        self.db.commit()
        AuditService(self.db).record(user_id=user_id, action="PAIEMENT_EN_LIGNE_INITIE", entity_type="paiement", entity_id=item.id, after={"statut": item.statut, "fournisseur": item.fournisseur})
        self.db.commit()
        return self._online_read(item)

    @staticmethod
    def _create_papi_link(*, amount: Decimal, reference: str, description: str, client_name: str, payer_phone: str | None, payer_email: str | None, provider: str) -> dict:
        payload = {
            "amount": int(amount),
            "clientName": client_name,
            "reference": reference,
            "description": description,
            "successUrl": f"{settings.frontend_url.rstrip('/')}/paiement/succes?reference={reference}",
            "failureUrl": f"{settings.frontend_url.rstrip('/')}/paiement/echec?reference={reference}",
            "notificationUrl": settings.papi_notification_url,
            "validDuration": settings.papi_valid_duration_hours,
            "provider": provider,
        }
        if payer_phone:
            payload["payerPhone"] = payer_phone
        if payer_email:
            payload["payerEmail"] = payer_email
        request = Request(
            f"{settings.papi_base_url.rstrip('/')}/payment-links",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Token": settings.papi_api_key or ""},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise HTTPException(502, f"Papi a refusé la demande de paiement ({exc.code}).") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise HTTPException(502, "Papi est momentanément indisponible.") from exc
        data = result.get("data") if isinstance(result, dict) else None
        if not isinstance(data, dict) or not data.get("paymentLink"):
            raise HTTPException(502, "Papi n'a pas retourné de lien de paiement.")
        return data

    def _online_read(self, item: Paiement) -> dict:
        paid = self.db.scalar(select(func.coalesce(func.sum(Paiement.montant), 0)).where(Paiement.id_reservation == item.id_reservation, Paiement.statut == PaiementStatus.VALIDE)) or Decimal("0")
        total = Decimal(item.reservation.montant_total) if item.reservation else Decimal(item.montant)
        return {
            "id_paiement": item.id, "statut": item.statut, "fournisseur": item.fournisseur or settings.payment_provider,
            "reference_paiement": item.reference_paiement or "", "montant": item.montant,
            "message": "Paiement en attente de confirmation de Papi." if item.statut == PaiementStatus.EN_ATTENTE else "Paiement traité.",
            "checkout_url": item.checkout_url,
            "acompte_minimum": self._minimum_deposit(total),
            "montant_restant": max(Decimal("0"), total - Decimal(paid)),
        }

    def handle_online_webhook(self, *, provider: str, payload: dict, signature: str | None, raw_body: bytes) -> dict:
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
        item = self.db.scalar(select(Paiement).where(Paiement.reference_paiement == raw, Paiement.fournisseur == "papi").with_for_update())
        if not item:
            raise HTTPException(404, "Paiement fournisseur introuvable.")
        if not item.notification_token or not hmac.compare_digest(item.notification_token, token):
            raise HTTPException(401, "Token de notification Papi invalide.")
        if Decimal(str(payload.get("amount", "0"))) != Decimal(item.montant):
            raise HTTPException(422, "Le montant du webhook Papi ne correspond pas à la réservation.")
        if item.statut == PaiementStatus.VALIDE:
            return {"id_paiement": item.id, "statut": item.statut, "idempotent": True}
        if status_value == "PENDING":
            return {"id_paiement": item.id, "statut": item.statut, "idempotent": True}
        item.statut = PaiementStatus.VALIDE if status_value == "SUCCESS" else PaiementStatus.ECHOUE
        item.webhook_recu_le = datetime.now(timezone.utc)
        item.reference_fournisseur = str(payload.get("paymentReference") or item.reference_fournisseur or raw)[:150]
        if status_value == "SUCCESS":
            reservation = item.reservation
            reservation.statut = ReservationStatus.PAYEE
            BilletService.issue_for_reservation(self.db, reservation)
            if reservation.id_user:
                NotificationService.add(self.db, user_id=reservation.id_user, type_notification="CONFIRMATION_PAIEMENT", titre="Paiement en ligne confirmé", message=f"Le paiement de la réservation {reservation.numero_reservation} est confirmé.", reservation_id=reservation.id, depart_id=reservation.id_depart)
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
