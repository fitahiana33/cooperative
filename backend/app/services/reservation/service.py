from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import hmac
import json
import logging
from math import ceil
import secrets
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet, BilletStatus
from app.models.depart import Depart, DepartStatus
from app.models.itineraire import Itineraire
from app.models.embarquement import Embarquement, EmbarquementStatus
from app.models.finance import Paiement, PaiementStatus
from app.models.place import DepartPlace, DepartPlaceStatus
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.models.tarif import Tarif
from app.models.user import User
from app.models.vehicule import Vehicule
from app.core.config import settings
from app.services.notification import NotificationService
from app.services.audit import AuditService
from app.services.billet import BilletService
from app.services.finance import FinanceService
from app.services.authentication.password import hash_password
from app.core.clock import local_moment, local_now, local_today


logger = logging.getLogger("cooperative.reservation")


class ReservationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _options():
        return (
            selectinload(Reservation.depart).selectinload(Depart.itineraire).selectinload(Itineraire.destination_depart),
            selectinload(Reservation.depart).selectinload(Depart.itineraire).selectinload(Itineraire.destination_arrivee),
            selectinload(Reservation.depart).selectinload(Depart.cooperative),
            selectinload(Reservation.depart).selectinload(Depart.vehicule).selectinload(Vehicule.modele),
            selectinload(Reservation.places).selectinload(ReservationPlace.depart_place),
            selectinload(Reservation.places).selectinload(ReservationPlace.billet),
        )

    def _get(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None, chauffeur_id: int | None = None, gare_ids: set[int] | None = None, lock: bool = False) -> Reservation:
        statement = select(Reservation).where(Reservation.id == reservation_id).options(*self._options())
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.join(Depart, Depart.id == Reservation.id_depart).where(Depart.id_cooperative.in_(cooperative_ids))
        if gare_ids is not None:
            statement = statement.where(Reservation.depart.has(Depart.id_gare.in_(gare_ids)))
        if chauffeur_id is not None:
            statement = statement.where(Reservation.depart.has(Depart.id_chauffeur == chauffeur_id))
        if lock:
            statement = statement.with_for_update(of=Reservation).execution_options(populate_existing=True)
        item = self.db.scalar(statement)
        if not item:
            raise HTTPException(404, "Réservation introuvable.")
        return item

    def _expire_if_needed(self, item: Reservation) -> None:
        now = datetime.now(timezone.utc)
        if item.statut == ReservationStatus.EN_ATTENTE and item.date_expiration and item.date_expiration <= now:
            item.statut = ReservationStatus.EXPIREE
            for place in item.places:
                if place.depart_place and place.depart_place.statut == DepartPlaceStatus.RESERVEE:
                    place.depart_place.statut = DepartPlaceStatus.DISPONIBLE
                if place.billet:
                    place.billet.statut = BilletStatus.ANNULE
            self.db.commit()

    def list_reservations(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        statut: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        id_cooperative: int | None = None,
        id_gare: int | None = None,
        id_itineraire: int | None = None,
        id_depart: int | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        owner_id: int | None = None,
        cooperative_ids: set[int] | None = None, chauffeur_id: int | None = None, gare_ids: set[int] | None = None,
        for_export: bool = False,
    ):
        statement = select(Reservation).options(*self._options()).join(Depart, Depart.id == Reservation.id_depart)
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        if gare_ids is not None:
            statement = statement.where(Depart.id_gare.in_(gare_ids))
        if chauffeur_id is not None:
            statement = statement.where(Depart.id_chauffeur == chauffeur_id)
        if id_cooperative is not None:
            statement = statement.where(Depart.id_cooperative == id_cooperative)
        if id_gare is not None:
            statement = statement.where(Depart.id_gare == id_gare)
        if id_itineraire is not None:
            statement = statement.where(Depart.id_itineraire == id_itineraire)
        if id_depart is not None:
            statement = statement.where(Depart.id == id_depart)
        if search and search.strip():
            statement = statement.where(Reservation.numero_reservation.ilike(f"%{search.strip()}%"))
        if statut:
            statement = statement.where(Reservation.statut == statut)
        if date_from:
            statement = statement.where(Depart.date_depart >= date_from)
        if date_to:
            statement = statement.where(Depart.date_depart <= date_to)
        total = self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        sort_columns = {
            "created_at": Reservation.created_at,
            "date_expiration": Reservation.date_expiration,
            "montant_total": Reservation.montant_total,
            "statut": Reservation.statut,
            "date_depart": Depart.date_depart,
        }
        sort_column = sort_columns.get(sort_by, Reservation.created_at)
        ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        if for_export:
            return self.db.scalars(statement.order_by(ordering, Reservation.id.desc()).execution_options(yield_per=500))
        items = list(self.db.scalars(statement.order_by(ordering, Reservation.id.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def list_places(self, depart_id: int, *, include_unavailable: bool = True) -> list[DepartPlace]:
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        statement = select(DepartPlace).where(DepartPlace.id_depart == depart_id).order_by(DepartPlace.numero_place)
        if not include_unavailable:
            statement = statement.where(DepartPlace.statut == DepartPlaceStatus.DISPONIBLE)
        return list(self.db.scalars(statement))

    def manifest_rows(self, depart_id: int) -> list[dict]:
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        statement = (
            select(Reservation)
            .where(
                Reservation.id_depart == depart_id,
                Reservation.statut.notin_([ReservationStatus.ANNULEE, ReservationStatus.EXPIREE]),
            )
            .options(*self._options())
            .order_by(Reservation.id)
        )
        boardings = self.db.scalars(select(Embarquement).join(Billet, Billet.id == Embarquement.id_billet)
            .join(ReservationPlace, ReservationPlace.id == Billet.id_reservation_place)
            .join(Reservation, Reservation.id == ReservationPlace.id_reservation)
            .where(Reservation.id_depart == depart_id)
            .order_by(Embarquement.id_billet, (Embarquement.statut == EmbarquementStatus.VALIDE).desc(),
                      Embarquement.date_heure_embarquement.desc(), Embarquement.id.desc()))
        boarding_by_ticket = {}
        for boarding in boardings:
            boarding_by_ticket.setdefault(boarding.id_billet, boarding)
        rows: list[dict] = []
        for reservation in self.db.scalars(statement).unique():
            for reservation_place in sorted(reservation.places, key=lambda item: item.depart_place.numero_place if item.depart_place else 0):
                billet = reservation_place.billet
                boarding = boarding_by_ticket.get(billet.id) if billet else None
                rows.append({
                    "reservation": reservation.numero_reservation,
                    "passager": reservation_place.nom_passager,
                    "telephone": reservation_place.telephone_passager or "",
                    "place": reservation_place.depart_place.numero_place if reservation_place.depart_place else "",
                    "billet": billet.numero_billet if billet else "",
                    "reservation_statut": reservation.statut,
                    "billet_statut": billet.statut if billet else "",
                    "pointage": boarding.statut if boarding else "NON_POINTÉ",
                    "date_pointage": boarding.date_heure_embarquement.isoformat() if boarding else "",
                    "embarque": bool(billet and billet.statut == BilletStatus.UTILISE),
                })
        return rows

    def _get_open_depart(self, depart_id: int) -> Depart:
        from app.services.depart.status import mark_overdue_departures

        # The scheduled task normally handles this. Repeat it at the sale
        # boundary so a disabled/restarting scheduler cannot keep sales open.
        mark_overdue_departures(self.db, commit=False)
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        if depart.date_depart < local_today():
            raise HTTPException(422, "Ce départ est déjà passé.")
        if not depart.cooperative.is_active or (depart.gare is not None and not depart.gare.is_active):
            raise HTTPException(422, "La gare et la coopérative doivent être actives pour accepter une réservation.")
        if not depart.itineraire.is_active:
            raise HTTPException(422, "L'itinéraire de ce départ n'est plus actif.")
        if not depart.vehicule.is_active or not depart.vehicule.disponibilite or depart.vehicule.etat == "HORS_SERVICE":
            raise HTTPException(422, "Le véhicule de ce départ n'est plus disponible. Contactez la coopérative.")
        if not depart.chauffeur.is_active or not depart.chauffeur.disponibilite or depart.chauffeur.date_expiration_permis < depart.date_depart:
            raise HTTPException(422, "Le chauffeur de ce départ n'est plus disponible pour ce voyage.")
        if depart.statut in {DepartStatus.ANNULE, DepartStatus.TERMINE, DepartStatus.PARTI}:
            raise HTTPException(422, "Ce départ n'accepte plus de réservation.")
        # A delayed or boarding departure may still take passengers after its
        # scheduled time; a merely scheduled one may not.
        from app.services.booking_policy import booking_policy
        from app.services.depart.status import booking_deadline, booking_is_open

        close_minutes = int(booking_policy(self.db)["booking_close_minutes"])
        if not booking_is_open(depart, close_minutes):
            deadline = booking_deadline(depart, close_minutes)
            raise HTTPException(
                422,
                "Les rÃ©servations sont fermÃ©es depuis "
                f"{deadline.strftime('%H:%M')} pour prÃ©parer le dÃ©part.",
            )
        return depart

    def _sync_depart_place_status(self, place_id: int, statut: DepartPlaceStatus) -> None:
        place = self.db.get(DepartPlace, place_id)
        if place is None:
            return
        place.statut = statut

    def create_reservation(self, *, user: User, depart_id: int, places: list[dict], as_passenger: bool = False, commit: bool = True) -> Reservation:
        depart = self._get_open_depart(depart_id)
        if not places:
            raise HTTPException(422, "Sélectionnez au moins une place.")
        if len({item["id_depart_place"] for item in places}) != len(places):
            raise HTTPException(422, "Une même place ne peut pas être sélectionnée plusieurs fois.")
        now = datetime.now(timezone.utc)
        if as_passenger:
            self.db.execute(select(User.id).where(User.id == user.id).with_for_update())
            self._check_passenger_limits(user.id, len(places), now)
        # The hold period is decided by the server, never by the client.
        expiration = now + timedelta(minutes=settings.reservation_hold_minutes)

        place_ids = sorted({int(item["id_depart_place"]) for item in places})
        locked_places = list(self.db.scalars(
            select(DepartPlace).where(DepartPlace.id.in_(place_ids)).order_by(DepartPlace.id).with_for_update()
        ))
        if len(locked_places) != len(place_ids) or any(place.id_depart != depart_id for place in locked_places):
            raise HTTPException(422, "Une place sélectionnée ne correspond pas à ce départ.")
        if any(place.statut != DepartPlaceStatus.DISPONIBLE for place in locked_places):
            raise HTTPException(409, "Une des places sélectionnées n'est plus disponible.")

        tarif = self.db.get(Tarif, depart.id_tarif)
        if not tarif:
            raise HTTPException(500, "Le tarif du départ est introuvable.")
        from app.services.booking_policy import booking_policy
        policy = booking_policy(self.db)
        reservation = Reservation(
            numero_reservation=f"RES-{uuid4().hex[:22].upper()}",
            id_depart=depart_id,
            id_user=user.id,
            montant_total=Decimal(tarif.prix) * len(places),
            taux_acompte=Decimal(str(policy["deposit_rate"])),
            plancher_acompte=Decimal(policy["minimum_deposit_amount"]),
            statut=ReservationStatus.EN_ATTENTE,
            date_expiration=expiration,
        )
        self.db.add(reservation)
        try:
            self.db.flush()
            fallback_name = self._fallback_passenger_name(places, user)
            by_id = {item["id_depart_place"]: item for item in places}
            for place in locked_places:
                data = by_id[place.id]
                self.db.add(ReservationPlace(
                    id_reservation=reservation.id,
                    id_depart_place=place.id,
                    nom_passager=self._clean_passenger_name(data.get("nom_passager"), fallback_name),
                    telephone_passager=data.get("telephone_passager"),
                ))
            if commit:
                self.db.commit()
            else:
                self.db.flush()
            return self._get(reservation.id)
        except (IntegrityError, SQLAlchemyError) as exc:
            self.db.rollback()
            logger.exception("Erreur création réservation", exc_info=exc)
            if isinstance(exc, IntegrityError):
                raise HTTPException(409, "Une des places sélectionnées a été réservée entre-temps.")
            raise HTTPException(500, "La réservation n'a pas pu être enregistrée.")

    def create_public_reservation(
        self,
        *,
        depart_id: int,
        places: list[dict],
        name: str,
        telephone: str,
        email: str | None,
        user: User | None = None,
        command_key: str | None = None,
    ) -> tuple[Reservation, str]:
        """Create a public reservation and attach it to a logged-in user when available."""
        key = command_key or secrets.token_urlsafe(32)
        command_hash = hashlib.sha256(key.encode()).hexdigest()
        payload = {"depart": depart_id, "places": sorted(places, key=lambda item: item["id_depart_place"]),
                   "name": name, "telephone": telephone, "email": email, "owner": user.id if user else None}
        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        access_token = hmac.new(settings.secret_key.encode(), ("booking:" + key).encode(), hashlib.sha256).hexdigest()
        # Serialize retries before looking up the command. Never store the access secret.
        lock_id = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big", signed=True)
        self.db.execute(select(func.pg_advisory_xact_lock(lock_id)))
        existing = self.db.scalar(select(Reservation).where(Reservation.commande_hash == command_hash))
        if existing:
            if existing.commande_payload_hash != payload_hash:
                raise HTTPException(409, "Cette demande existe avec des informations différentes.")
            return self._get(existing.id), access_token
        if len(places) > settings.passenger_max_seats_per_reservation:
            raise HTTPException(422, f"Vous pouvez réserver au maximum {settings.passenger_max_seats_per_reservation} places.")
        telephone = "".join(c for c in telephone if c.isdigit())
        if len(telephone) < 8:
            raise HTTPException(422, "Renseignez un téléphone valide.")
        phone_lock = int.from_bytes(hashlib.sha256(("phone:" + telephone).encode()).digest()[:8], "big", signed=True)
        self.db.execute(select(func.pg_advisory_xact_lock(phone_lock)))
        pending = self.db.scalar(select(func.count()).select_from(Reservation).where(
            Reservation.telephone_reservataire == telephone, Reservation.statut == ReservationStatus.EN_ATTENTE,
            Reservation.date_expiration > datetime.now(timezone.utc))) or 0
        if pending >= settings.passenger_max_pending_reservations:
            raise HTTPException(409, "Ce téléphone possède déjà des réservations en attente de paiement.")
        owner = user
        if owner is None:
            owner = User(name=name[:100], email=f"guest-{uuid4().hex}@guest.cooperative.local",
                         telephone=telephone, password_hash=hash_password(secrets.token_urlsafe(32)), is_active=False)
            self.db.add(owner)
            self.db.flush()
        item = self.create_reservation(user=owner, depart_id=depart_id, places=places, as_passenger=True, commit=False)
        item.nom_reservataire = name
        item.telephone_reservataire = telephone
        item.email_reservataire = email
        item.acces_public_hash = hashlib.sha256(access_token.encode()).hexdigest()
        item.commande_hash = command_hash
        item.commande_payload_hash = payload_hash
        AuditService(self.db).record(user_id=user.id if user else None, action="RESERVATION_PUBLIQUE_CREEE",
            entity_type="reservation", entity_id=item.id, after={"statut": item.statut})
        self.db.commit()
        return self._get(item.id), access_token

    def get_public_reservation(self, reservation_number: str, access_token: str) -> Reservation:
        item = self.db.scalar(
            select(Reservation).where(Reservation.numero_reservation == reservation_number).options(*self._options())
        )
        expected = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        if not item or not item.acces_public_hash or not secrets.compare_digest(item.acces_public_hash, expected):
            raise HTTPException(404, "Réservation introuvable.")
        self._expire_if_needed(item)
        return item

    def update_reservation(
        self,
        reservation_id: int,
        *,
        depart_id: int,
        places: list[dict],
        owner_id: int | None = None,
        cooperative_ids: set[int] | None = None, chauffeur_id: int | None = None, gare_ids: set[int] | None = None,
        default_passenger_name: str | None = None,
    ) -> Reservation:
        """Replace an unpaid reservation's trip, seats and passenger details atomically."""
        item = self._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=chauffeur_id, gare_ids=gare_ids, lock=True)
        if item.statut != ReservationStatus.EN_ATTENTE:
            raise HTTPException(409, "Seule une réservation en attente de paiement peut être modifiée.")
        self._expire_if_needed(item)
        if item.statut == ReservationStatus.EXPIREE:
            raise HTTPException(409, "Cette réservation a expiré ; créez une nouvelle réservation.")
        if item.acces_public_hash or self.db.scalar(select(Paiement.id).where(
            Paiement.id_reservation == item.id, Paiement.statut == PaiementStatus.EN_ATTENTE,
        ).limit(1)):
            raise HTTPException(409, "Une demande de paiement est déjà associée à cette réservation ; elle ne peut plus être modifiée.")
        if not places:
            raise HTTPException(422, "Sélectionnez au moins une place.")

        depart = self._get_open_depart(depart_id)
        place_ids = sorted({int(value["id_depart_place"]) for value in places})
        if len(place_ids) != len(places):
            raise HTTPException(422, "Une même place ne peut pas être sélectionnée plusieurs fois.")
        if chauffeur_id is not None and depart.id_chauffeur != chauffeur_id:
            raise HTTPException(403, "Le nouveau départ ne vous est pas affecté.")
        if gare_ids is not None and depart.id_gare not in gare_ids:
            raise HTTPException(403, "Le nouveau départ ne relève pas de votre gare.")
        if cooperative_ids is not None and depart.id_cooperative not in cooperative_ids:
            raise HTTPException(403, "Le nouveau départ ne relève pas de vos coopératives.")
        locked_places = list(self.db.scalars(
            select(DepartPlace).where(DepartPlace.id.in_(place_ids)).order_by(DepartPlace.id).with_for_update()
        ))
        if len(locked_places) != len(place_ids) or any(place.id_depart != depart_id for place in locked_places):
            raise HTTPException(422, "Une place sélectionnée ne correspond pas à ce départ.")

        if owner_id is not None and len(places) > settings.passenger_max_seats_per_reservation:
            raise HTTPException(422, f"Vous pouvez rÃ©server au maximum {settings.passenger_max_seats_per_reservation} places Ã  la fois.")

        current_ids = {row.id_depart_place for row in item.places}
        if any(place.statut != DepartPlaceStatus.DISPONIBLE and place.id not in current_ids for place in locked_places):
            raise HTTPException(409, "Une des places sélectionnées n'est plus disponible.")

        tarif = self.db.get(Tarif, depart.id_tarif)
        if not tarif:
            raise HTTPException(500, "Le tarif du départ est introuvable.")

        old_places = list(item.places)
        for row in old_places:
            if row.depart_place and row.depart_place.id not in place_ids:
                row.depart_place.statut = DepartPlaceStatus.DISPONIBLE
        # Pending reservations have no issued tickets yet, so replacing their
        # rows cannot orphan a ticket or change a paid amount retroactively.
        item.id_depart = depart_id
        item.montant_total = Decimal(tarif.prix) * len(places)
        item.date_expiration = datetime.now(timezone.utc) + timedelta(minutes=settings.reservation_hold_minutes)
        old_by_place_id = {row.id_depart_place: row for row in old_places}
        for row in old_places:
            if row.id_depart_place not in place_ids:
                self.db.delete(row)
        by_id = {value["id_depart_place"]: value for value in places}
        fallback_name = self._fallback_passenger_name(places, None, default_passenger_name or next((row.nom_passager for row in old_places if row.nom_passager), None))
        for place in locked_places:
            value = by_id[place.id]
            row = old_by_place_id.get(place.id)
            if row is None:
                item.places.append(ReservationPlace(
                    id_depart_place=place.id,
                    nom_passager=self._clean_passenger_name(value.get("nom_passager"), fallback_name),
                    telephone_passager=value.get("telephone_passager"),
                ))
            else:
                row.nom_passager = self._clean_passenger_name(value.get("nom_passager"), fallback_name)
                row.telephone_passager = value.get("telephone_passager")
        NotificationService.add(
            self.db,
            user_id=item.id_user,
            type_notification="MODIFICATION_RESERVATION",
            titre="Réservation modifiée",
            message=f"Votre réservation {item.numero_reservation} a été modifiée. Vérifiez les nouvelles places et le nouveau montant.",
            reservation_id=item.id,
            depart_id=item.id_depart,
        )
        try:
            self.db.commit()
            return self._get(item.id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=chauffeur_id, gare_ids=gare_ids)
        except (IntegrityError, SQLAlchemyError) as exc:
            self.db.rollback()
            logger.exception("Erreur modification réservation", exc_info=exc)
            if isinstance(exc, IntegrityError):
                raise HTTPException(409, "Une des places sélectionnées a été réservée entre-temps.")
            raise HTTPException(500, "La modification de la réservation n'a pas pu être enregistrée.")

    @staticmethod
    def _clean_passenger_name(value: str | None, fallback: str) -> str:
        name = " ".join(str(value or "").split())
        return name if len(name) >= 2 else fallback

    @classmethod
    def _fallback_passenger_name(cls, places: list[dict], user: User | None, explicit: str | None = None) -> str:
        candidates = [explicit]
        candidates.extend(item.get("nom_passager") for item in places)
        if user is not None:
            candidates.append(f"{user.first_name or ''} {user.name or ''}")
        for candidate in candidates:
            cleaned = " ".join(str(candidate or "").split())
            if len(cleaned) >= 2:
                return cleaned[:150]
        return "Passager"

    def _check_passenger_limits(self, user_id: int, seat_count: int, now: datetime) -> None:
        if seat_count > settings.passenger_max_seats_per_reservation:
            raise HTTPException(422, f"Vous pouvez réserver au maximum {settings.passenger_max_seats_per_reservation} places à la fois.")
        pending = self.db.scalar(
            select(func.count()).select_from(Reservation).where(
                Reservation.id_user == user_id,
                Reservation.statut == ReservationStatus.EN_ATTENTE,
                Reservation.date_expiration > now,
            )
        ) or 0
        if pending >= settings.passenger_max_pending_reservations:
            raise HTTPException(409, "Vous avez déjà des réservations en attente de paiement. Payez-les ou attendez leur expiration avant d'en créer une autre.")

    def confirm(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None, chauffeur_id: int | None = None, gare_ids: set[int] | None = None, commit: bool = True) -> Reservation:
        item = self._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=chauffeur_id, gare_ids=gare_ids, lock=True)
        if item.statut != ReservationStatus.EN_ATTENTE:
            raise HTTPException(409, "Seule une réservation en attente peut être confirmée.")
        try:
            self._get_open_depart(item.id_depart)
        except HTTPException as exc:
            raise HTTPException(409, exc.detail)
        if item.date_expiration and item.date_expiration <= datetime.now(timezone.utc):
            item.statut = ReservationStatus.EXPIREE
            self.db.commit()
            raise HTTPException(409, "Le délai de confirmation de cette réservation est dépassé.")
        item.statut = ReservationStatus.CONFIRMEE
        BilletService.issue_for_reservation(self.db, item)
        NotificationService.add(
            self.db,
            user_id=item.id_user,
            type_notification="CONFIRMATION_RESERVATION",
            titre="Réservation confirmée",
            message=f"Votre réservation {item.numero_reservation} est confirmée.",
            reservation_id=item.id,
            depart_id=item.id_depart,
        )
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return self._get(item.id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=chauffeur_id, gare_ids=gare_ids)

    def cancel(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None, chauffeur_id: int | None = None, caisse_id: int | None = None, agent_id: int | None = None, gare_ids: set[int] | None = None, can_refund_now: bool = False) -> Reservation:
        """Cancel a reservation and free its seats.

        Paid money is returned from a cash desk at once when the caller may
        handle cash (`can_refund_now`) and named an open desk; otherwise the
        payment is flagged for a cashier to refund.
        """
        item = self._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=chauffeur_id, gare_ids=gare_ids if owner_id is None else None, lock=True)
        if item.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être annulée.")
        if any(place.billet and place.billet.statut == BilletStatus.UTILISE for place in item.places):
            raise HTTPException(409, "Un passager a déjà embarqué ; cette réservation ne peut plus être annulée.")
        depart = item.depart
        if depart.statut in {DepartStatus.PARTI, DepartStatus.TERMINE}:
            raise HTTPException(409, "Le départ a déjà eu lieu : la réservation ne peut plus être annulée.")
        payments = list(self.db.scalars(select(Paiement).where(Paiement.id_reservation == item.id, Paiement.statut == PaiementStatus.VALIDE)))
        if payments and owner_id is not None and depart.statut != DepartStatus.ANNULE:
            deadline = local_moment(depart.date_depart, depart.heure_depart) - timedelta(minutes=settings.cancellation_deadline_minutes)
            if local_now() > deadline:
                hours = settings.cancellation_deadline_minutes // 60
                raise HTTPException(409, f"Une réservation payée ne peut plus être annulée moins de {hours} h avant le départ.")
        finance = FinanceService(self.db)
        for payment in payments:
            if can_refund_now and caisse_id:
                finance.refund(payment.id, caisse_id=caisse_id, agent_id=agent_id or item.id_user, gare_ids=gare_ids, commit=False)
            else:
                finance.request_refund(payment)
        item.statut = ReservationStatus.ANNULEE
        for place in item.places:
            if place.depart_place is not None:
                place.depart_place.statut = DepartPlaceStatus.DISPONIBLE
            if place.billet:
                place.billet.statut = BilletStatus.ANNULE
        NotificationService.add(
            self.db,
            user_id=item.id_user,
            type_notification="ANNULATION",
            titre="Réservation annulée",
            message=f"Votre réservation {item.numero_reservation} a été annulée.",
            reservation_id=item.id,
            depart_id=item.id_depart,
        )
        self.db.commit()
        return self._get(item.id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=chauffeur_id, gare_ids=gare_ids if owner_id is None else None)

    def update_place_status(self, place_id: int, statut: str) -> DepartPlace:
        item = self.db.get(DepartPlace, place_id, with_for_update=True, populate_existing=True)
        if not item:
            raise HTTPException(404, "Place introuvable.")
        if item.statut in {DepartPlaceStatus.RESERVEE, DepartPlaceStatus.OCCUPEE}:
            raise HTTPException(409, "Une place réservée ou occupée ne peut pas être bloquée manuellement.")
        if statut not in {DepartPlaceStatus.DISPONIBLE, DepartPlaceStatus.BLOQUEE}:
            raise HTTPException(422, "Une place peut uniquement être disponible ou bloquée manuellement.")
        item.statut = statut
        self.db.commit()
        self.db.refresh(item)
        return item
