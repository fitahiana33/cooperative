import logging

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.pagination import paginate
from app.models import Emplacement, Gare, Quai, Zone

logger = logging.getLogger("cooperative.gare")


class GareService:
    def __init__(self, db: Session):
        self.db = db

    def list_gares(self, **kwargs):
        return paginate(
            self.db, Gare, page=kwargs.get("page", 1), page_size=kwargs.get("page_size", 20),
            search=kwargs.get("search"), search_fields=("nom", "ville", "adresse"),
            sort_by=kwargs.get("sort_by", "nom"),
            sort_fields=("nom", "ville", "adresse", "created_at"),
            sort_order=kwargs.get("sort_order", "asc"),
        )

    def get_gare(self, gare_id: int) -> Gare:
        gare = self.db.get(Gare, gare_id)
        if not gare:
            raise HTTPException(404, "Gare introuvable.")
        return gare

    def create_gare(self, *, nom: str, ville: str, adresse: str, latitude=None, longitude=None, **fields) -> Gare:
        clean_name = nom.strip()
        clean_city = ville.strip()
        clean_address = adresse.strip()
        if not clean_name or not clean_city or not clean_address:
            raise HTTPException(422, "Le nom, la ville et l'adresse de la gare sont obligatoires.")
        if self.db.scalar(select(Gare).where(func.lower(Gare.nom) == clean_name.lower())):
            raise HTTPException(400, "Une gare portant ce nom existe deja.")
        gare = Gare(
            nom=clean_name, ville=clean_city, adresse=clean_address,
            latitude=latitude, longitude=longitude,
            **{key: value for key, value in fields.items() if hasattr(Gare, key)},
        )
        try:
            self.db.add(gare)
            self.db.commit()
            self.db.refresh(gare)
            return gare
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Les informations de cette gare sont invalides.")

    def update_gare(self, gare_id: int, **fields) -> Gare:
        gare = self.get_gare(gare_id)
        for required in ("nom", "ville", "adresse"):
            if required in fields and fields[required] is not None and not fields[required].strip():
                raise HTTPException(422, "Le nom, la ville et l'adresse de la gare ne peuvent pas etre vides.")
        if fields.get("nom") and fields["nom"].strip().lower() != gare.nom.lower():
            duplicate = self.db.scalar(select(Gare).where(
                Gare.id != gare_id,
                func.lower(Gare.nom) == fields["nom"].strip().lower(),
            ))
            if duplicate:
                raise HTTPException(400, "Une gare portant ce nom existe deja.")
        for key, value in fields.items():
            if (value is not None or key in {"region", "telephone", "email", "description", "latitude", "longitude"}) and hasattr(Gare, key):
                setattr(gare, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            self.db.refresh(gare)
            return gare
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Les informations de cette gare sont invalides.")

    def toggle_gare(self, gare_id: int) -> Gare:
        gare = self.get_gare(gare_id)
        gare.is_active = not gare.is_active
        self.db.commit()
        self.db.refresh(gare)
        return gare

    def delete_gare(self, gare_id: int) -> None:
        gare = self.get_gare(gare_id)
        self.db.delete(gare)
        self.db.commit()

    def add_quai(self, gare_id: int, *, numero: str, nom=None, description=None) -> Quai:
        gare = self.get_gare(gare_id)
        if not gare.is_active:
            raise HTTPException(422, "Une gare inactive ne peut pas recevoir de nouveau quai.")
        clean_number = numero.strip()
        if not clean_number:
            raise HTTPException(422, "Le numero du quai est obligatoire.")
        item = Quai(id_gare=gare_id, numero=clean_number, nom=nom, description=description)
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Ce numero de quai existe deja dans cette gare.")

    def list_quais(self, gare_id: int) -> list[Quai]:
        self.get_gare(gare_id)
        return list(self.db.scalars(select(Quai).where(Quai.id_gare == gare_id).order_by(Quai.numero)))

    def update_quai(self, gare_id: int, quai_id: int, **fields) -> Quai:
        self.get_gare(gare_id)
        item = self.db.scalar(select(Quai).where(Quai.id == quai_id, Quai.id_gare == gare_id))
        if not item:
            raise HTTPException(404, "Quai introuvable.")
        if fields.get("numero") is not None and not fields["numero"].strip():
            raise HTTPException(422, "Le numero du quai est obligatoire.")
        for key, value in fields.items():
            if value is not None and hasattr(Quai, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Ce numero de quai existe deja dans cette gare.")

    def delete_quai(self, gare_id: int, quai_id: int) -> None:
        self.update_quai(gare_id, quai_id, is_active=False)

    def toggle_quai(self, gare_id: int, quai_id: int) -> Quai:
        item = self.update_quai(gare_id, quai_id)
        return self.update_quai(gare_id, quai_id, is_active=not item.is_active)

    def add_zone(self, gare_id: int, *, nom: str, type_zone=None, description=None) -> Zone:
        gare = self.get_gare(gare_id)
        if not gare.is_active:
            raise HTTPException(422, "Une gare inactive ne peut pas recevoir de nouvelle zone.")
        clean_name = nom.strip()
        if not clean_name:
            raise HTTPException(422, "Le nom de la zone est obligatoire.")
        item = Zone(id_gare=gare_id, nom=clean_name, type_zone=type_zone, description=description)
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Les informations de cette zone sont invalides.")

    def list_zones(self, gare_id: int) -> list[Zone]:
        self.get_gare(gare_id)
        return list(self.db.scalars(select(Zone).where(Zone.id_gare == gare_id).order_by(Zone.nom)))

    def update_zone(self, gare_id: int, zone_id: int, **fields) -> Zone:
        self.get_gare(gare_id)
        item = self.db.scalar(select(Zone).where(Zone.id == zone_id, Zone.id_gare == gare_id))
        if not item:
            raise HTTPException(404, "Zone introuvable.")
        if fields.get("nom") is not None and not fields["nom"].strip():
            raise HTTPException(422, "Le nom de la zone est obligatoire.")
        for key, value in fields.items():
            if value is not None and hasattr(Zone, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Les informations de cette zone sont invalides.")

    def delete_zone(self, gare_id: int, zone_id: int) -> None:
        self.update_zone(gare_id, zone_id, is_active=False)

    def toggle_zone(self, gare_id: int, zone_id: int) -> Zone:
        item = self.update_zone(gare_id, zone_id)
        return self.update_zone(gare_id, zone_id, is_active=not item.is_active)

    def add_emplacement(self, zone_id: int, *, code: str, nom=None, type_emplacement=None, description=None) -> Emplacement:
        zone = self.db.get(Zone, zone_id)
        if not zone:
            raise HTTPException(404, "Zone introuvable.")
        if not zone.is_active or not zone.gare.is_active:
            raise HTTPException(422, "Une zone inactive ou une gare inactive ne peut pas recevoir d'emplacement.")
        clean_code = code.strip()
        if not clean_code:
            raise HTTPException(422, "Le code de l'emplacement est obligatoire.")
        item = Emplacement(
            id_zone=zone_id, code=clean_code, nom=nom,
            type_emplacement=type_emplacement, description=description,
        )
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Ce code d emplacement existe deja dans cette zone.")

    def list_emplacements(self, gare_id: int, zone_id: int) -> list[Emplacement]:
        self.get_gare(gare_id)
        if not self.db.scalar(select(Zone).where(Zone.id == zone_id, Zone.id_gare == gare_id)):
            raise HTTPException(404, "Zone introuvable.")
        return list(self.db.scalars(select(Emplacement).where(Emplacement.id_zone == zone_id).order_by(Emplacement.code)))

    def update_emplacement(self, gare_id: int, zone_id: int, emplacement_id: int, **fields) -> Emplacement:
        self.get_gare(gare_id)
        if not self.db.scalar(select(Zone).where(Zone.id == zone_id, Zone.id_gare == gare_id)):
            raise HTTPException(404, "Zone introuvable.")
        item = self.db.scalar(select(Emplacement).where(Emplacement.id == emplacement_id, Emplacement.id_zone == zone_id))
        if not item:
            raise HTTPException(404, "Emplacement introuvable.")
        for key, value in fields.items():
            if value is not None and hasattr(Emplacement, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Les informations de l emplacement sont invalides.")

    def delete_emplacement(self, gare_id: int, zone_id: int, emplacement_id: int) -> None:
        self.update_emplacement(gare_id, zone_id, emplacement_id, is_active=False)

    def toggle_emplacement(self, gare_id: int, zone_id: int, emplacement_id: int) -> Emplacement:
        item = self.update_emplacement(gare_id, zone_id, emplacement_id)
        return self.update_emplacement(gare_id, zone_id, emplacement_id, is_active=not item.is_active)
