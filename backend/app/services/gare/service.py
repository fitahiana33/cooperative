import logging

from fastapi import HTTPException
from sqlalchemy import select
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
        if self.db.scalar(select(Gare).where(Gare.nom == nom.strip())):
            raise HTTPException(400, "Une gare portant ce nom existe deja.")
        gare = Gare(
            nom=nom.strip(), ville=ville.strip(), adresse=adresse.strip(),
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
        for key, value in fields.items():
            if value is not None and hasattr(Gare, key):
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
        self.get_gare(gare_id)
        item = Quai(id_gare=gare_id, numero=numero.strip(), nom=nom, description=description)
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

    def add_zone(self, gare_id: int, *, nom: str, type_zone=None, description=None) -> Zone:
        self.get_gare(gare_id)
        item = Zone(id_gare=gare_id, nom=nom.strip(), type_zone=type_zone, description=description)
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

    def add_emplacement(self, zone_id: int, *, code: str, nom=None, type_emplacement=None, description=None) -> Emplacement:
        if not self.db.get(Zone, zone_id):
            raise HTTPException(404, "Zone introuvable.")
        item = Emplacement(
            id_zone=zone_id, code=code.strip(), nom=nom,
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
