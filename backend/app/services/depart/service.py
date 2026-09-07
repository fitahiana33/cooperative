from datetime import date, time
import logging
from math import ceil

from fastapi import HTTPException
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.chauffeur import Chauffeur
from app.models.cooperative import Cooperative
from app.models.depart import Depart, DepartStatus
from app.models.itineraire import Itineraire, ItineraireCooperative
from app.models.tarif import Tarif
from app.models.vehicule import Vehicule, VehiculeChauffeur

logger = logging.getLogger("cooperative.depart")


class DepartService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _options():
        return (
            selectinload(Depart.itineraire).selectinload(Itineraire.destination_depart),
            selectinload(Depart.itineraire).selectinload(Itineraire.destination_arrivee),
            selectinload(Depart.cooperative),
            selectinload(Depart.vehicule),
            selectinload(Depart.chauffeur),
            selectinload(Depart.tarif),
        )

    def _get(self, depart_id: int, cooperative_ids: set[int] | None = None) -> Depart:
        item = self.db.scalar(
            select(Depart).where(Depart.id == depart_id).options(*self._options())
        )
        if not item:
            raise HTTPException(404, "Départ introuvable.")
        if cooperative_ids is not None and item.id_cooperative not in cooperative_ids:
            raise HTTPException(404, "Départ introuvable.")
        return item

    def list_departs(
        self,
        *,
        page=1,
        page_size=20,
        search=None,
        sort_by="date_depart",
        sort_order="asc",
        statut=None,
        id_cooperative=None,
        date_from: date | None = None,
        date_to: date | None = None,
        cooperative_ids: set[int] | None = None,
    ):
        if date_from and date_to and date_to < date_from:
            raise HTTPException(422, "La date de fin ne peut pas être antérieure à la date de début.")

        statement = select(Depart).options(*self._options())
        if id_cooperative is not None:
            statement = statement.where(Depart.id_cooperative == id_cooperative)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        if statut:
            statement = statement.where(Depart.statut == statut)
        if date_from:
            statement = statement.where(Depart.date_depart >= date_from)
        if date_to:
            statement = statement.where(Depart.date_depart <= date_to)
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(Depart.statut.ilike(term))

        sort_column = {
            "date_depart": Depart.date_depart,
            "heure_depart": Depart.heure_depart,
            "created_at": Depart.created_at,
            "statut": Depart.statut,
        }.get(sort_by, Depart.date_depart)
        order = asc if sort_order == "asc" else desc
        statement = statement.order_by(order(sort_column), order(Depart.heure_depart), Depart.id)
        total = self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        items = list(
            self.db.scalars(
                statement.offset((page - 1) * page_size).limit(page_size)
            )
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": ceil(total / page_size) if total else 0,
        }

    def get_depart(self, depart_id: int, *, cooperative_ids: set[int] | None = None) -> Depart:
        return self._get(depart_id, cooperative_ids)

    def _validate_schedule(
        self,
        *,
        depart_id: int | None,
        id_itineraire: int,
        id_cooperative: int,
        id_vehicule: int,
        id_chauffeur: int,
        id_tarif: int,
        date_depart: date,
        heure_depart: time,
        nombre_places: int | None,
    ) -> int:
        if date_depart < date.today():
            raise HTTPException(422, "La date du départ ne peut pas être antérieure à aujourd'hui.")

        itinerary = self.db.get(Itineraire, id_itineraire)
        if not itinerary:
            raise HTTPException(404, "Itinéraire introuvable.")
        if not itinerary.is_active:
            raise HTTPException(422, "L'itinéraire sélectionné est inactif.")

        cooperative = self.db.get(Cooperative, id_cooperative)
        if not cooperative:
            raise HTTPException(404, "Coopérative introuvable.")
        if not cooperative.is_active:
            raise HTTPException(422, "La coopérative sélectionnée est inactive.")

        itinerary_cooperative = self.db.scalar(
            select(ItineraireCooperative).where(
                ItineraireCooperative.id_itineraire == id_itineraire,
                ItineraireCooperative.id_cooperative == id_cooperative,
                ItineraireCooperative.is_active.is_(True),
                ItineraireCooperative.date_debut <= date_depart,
                or_(
                    ItineraireCooperative.date_fin.is_(None),
                    ItineraireCooperative.date_fin >= date_depart,
                ),
            )
        )
        if not itinerary_cooperative:
            raise HTTPException(422, "La coopérative n'est pas autorisée sur cet itinéraire à cette date.")

        vehicle = self.db.get(Vehicule, id_vehicule)
        if not vehicle:
            raise HTTPException(404, "Véhicule introuvable.")
        if vehicle.id_cooperative != id_cooperative:
            raise HTTPException(400, "Le véhicule et la coopérative doivent correspondre.")
        if not vehicle.is_active or not vehicle.disponibilite:
            raise HTTPException(422, "Le véhicule doit être actif et disponible.")
        if vehicle.etat == "HORS_SERVICE":
            raise HTTPException(422, "Un véhicule hors service ne peut pas être programmé.")

        chauffeur = self.db.get(Chauffeur, id_chauffeur)
        if not chauffeur:
            raise HTTPException(404, "Chauffeur introuvable.")
        if chauffeur.id_cooperative != id_cooperative:
            raise HTTPException(400, "Le chauffeur et la coopérative doivent correspondre.")
        if not chauffeur.is_active or not chauffeur.disponibilite:
            raise HTTPException(422, "Le chauffeur doit être actif et disponible.")
        if chauffeur.date_expiration_permis < date_depart:
            raise HTTPException(422, "Le permis du chauffeur ne couvre pas la date du départ.")

        assignment = self.db.scalar(
            select(VehiculeChauffeur).where(
                VehiculeChauffeur.id_vehicule == id_vehicule,
                VehiculeChauffeur.id_chauffeur == id_chauffeur,
                VehiculeChauffeur.is_active.is_(True),
                VehiculeChauffeur.date_debut <= date_depart,
                or_(
                    VehiculeChauffeur.date_fin.is_(None),
                    VehiculeChauffeur.date_fin >= date_depart,
                ),
            )
        )
        if not assignment:
            raise HTTPException(422, "Le chauffeur doit être affecté à ce véhicule pour la date du départ.")

        tariff = self.db.get(Tarif, id_tarif)
        if not tariff:
            raise HTTPException(404, "Tarif introuvable.")
        if tariff.id_itineraire != id_itineraire:
            raise HTTPException(400, "Le tarif et l'itinéraire doivent correspondre.")
        if tariff.id_cooperative is not None and tariff.id_cooperative != id_cooperative:
            raise HTTPException(400, "Le tarif et la coopérative doivent correspondre.")
        if not tariff.is_active:
            raise HTTPException(422, "Le tarif sélectionné est inactif.")
        if tariff.date_debut > date_depart or (tariff.date_fin and tariff.date_fin < date_depart):
            raise HTTPException(422, "Le tarif ne couvre pas la date du départ.")

        capacity = nombre_places or vehicle.nombre_places
        if capacity > vehicle.nombre_places:
            raise HTTPException(422, "Le nombre de places ne peut pas dépasser la capacité du véhicule.")

        conflict = self.db.scalar(
            select(Depart).where(
                Depart.id != depart_id if depart_id is not None else True,
                Depart.statut != DepartStatus.ANNULE,
                Depart.date_depart == date_depart,
                Depart.heure_depart == heure_depart,
                or_(
                    Depart.id_vehicule == id_vehicule,
                    Depart.id_chauffeur == id_chauffeur,
                ),
            )
        )
        if conflict:
            raise HTTPException(409, "Le véhicule ou le chauffeur est déjà programmé à cette date et cette heure.")

        return capacity

    def create_depart(self, **fields) -> Depart:
        capacity = self._validate_schedule(depart_id=None, **fields)
        item = Depart(**fields, nombre_places=capacity, statut=DepartStatus.PROGRAMME, places_reservees=0)
        try:
            self.db.add(item)
            self.db.commit()
            return self._get(item.id)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Un départ existe déjà pour ce véhicule ou ce chauffeur à cette date et cette heure.")
        except Exception:
            self.db.rollback()
            logger.exception("Erreur création départ")
            raise HTTPException(500, "Une erreur est survenue lors de la création du départ.")

    def update_depart(self, depart_id: int, **fields) -> Depart:
        item = self._get(depart_id)
        if item.statut not in {DepartStatus.PROGRAMME, DepartStatus.RETARDE}:
            raise HTTPException(409, "Seuls les départs programmés ou retardés peuvent être modifiés.")

        values = {
            "id_itineraire": fields.get("id_itineraire", item.id_itineraire),
            "id_cooperative": fields.get("id_cooperative", item.id_cooperative),
            "id_vehicule": fields.get("id_vehicule", item.id_vehicule),
            "id_chauffeur": fields.get("id_chauffeur", item.id_chauffeur),
            "id_tarif": fields.get("id_tarif", item.id_tarif),
            "date_depart": fields.get("date_depart", item.date_depart),
            "heure_depart": fields.get("heure_depart", item.heure_depart),
            "nombre_places": fields.get("nombre_places", item.nombre_places),
        }
        values["nombre_places"] = self._validate_schedule(depart_id=depart_id, **values)
        for key, value in values.items():
            setattr(item, key, value)
        try:
            self.db.commit()
            return self._get(item.id)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Les informations du départ sont invalides ou entrent en conflit avec un autre départ.")

    def update_status(self, depart_id: int, statut: str) -> Depart:
        item = self._get(depart_id)
        current = DepartStatus(item.statut)
        target = DepartStatus(statut)
        transitions = {
            DepartStatus.PROGRAMME: {DepartStatus.EMBARQUEMENT, DepartStatus.RETARDE, DepartStatus.PARTI},
            DepartStatus.EMBARQUEMENT: {DepartStatus.RETARDE, DepartStatus.PARTI},
            DepartStatus.RETARDE: {DepartStatus.EMBARQUEMENT, DepartStatus.PARTI},
            DepartStatus.PARTI: {DepartStatus.TERMINE},
            DepartStatus.TERMINE: set(),
            DepartStatus.ANNULE: set(),
        }
        if target == DepartStatus.ANNULE:
            raise HTTPException(422, "Utilisez l'action d'annulation dédiée pour annuler un départ.")
        if target != current and target not in transitions[current]:
            raise HTTPException(409, "Cette transition de statut n'est pas autorisée.")
        item.statut = target
        self.db.commit()
        return self._get(item.id)

    def cancel_depart(self, depart_id: int) -> Depart:
        item = self._get(depart_id)
        if item.statut in {DepartStatus.ANNULE, DepartStatus.PARTI, DepartStatus.TERMINE}:
            raise HTTPException(409, "Ce départ ne peut plus être annulé.")
        item.statut = DepartStatus.ANNULE
        self.db.commit()
        return self._get(item.id)
