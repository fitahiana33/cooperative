from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.gare import (
    GareCreate, GareUpdate, GareRead, QuaiCreate, QuaiRead, QuaiUpdate,
    ZoneCreate, ZoneRead, ZoneUpdate, EmplacementCreate, EmplacementRead, EmplacementUpdate,
)
from app.schemas.common import PageResponse
from app.services.gare import GareService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/gares", tags=["gares"])

@router.get("", response_model=PageResponse[GareRead])
def list_gares(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("nom", pattern="^(nom|ville|adresse|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("GARE_READ")),
    db: Session = Depends(get_db),
):
    return GareService(db).list_gares(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("", response_model=GareRead, status_code=status.HTTP_201_CREATED)
def create_gare(
    data: GareCreate,
    _: User = Depends(require_permission("GARE_CREATE")),
    db: Session = Depends(get_db),
):
    return GareService(db).create_gare(
        nom=data.nom,
        ville=data.ville,
        adresse=data.adresse,
        latitude=data.latitude,
        longitude=data.longitude,
        region=data.region,
        telephone=data.telephone,
        email=data.email,
        description=data.description,
    )

@router.get("/{gare_id}", response_model=GareRead)
def get_gare(
    gare_id: int,
    _: User = Depends(require_permission("GARE_READ")),
    db: Session = Depends(get_db),
):
    return GareService(db).get_gare(gare_id)

@router.put("/{gare_id}", response_model=GareRead)
def update_gare(
    gare_id: int,
    data: GareUpdate,
    _: User = Depends(require_permission("GARE_UPDATE")),
    db: Session = Depends(get_db),
):
    return GareService(db).update_gare(gare_id, **data.model_dump(exclude_unset=True))

@router.patch("/{gare_id}/toggle", response_model=GareRead)
def toggle_gare(
    gare_id: int,
    _: User = Depends(require_permission("GARE_UPDATE")),
    db: Session = Depends(get_db),
):
    return GareService(db).toggle_gare(gare_id)

@router.delete("/{gare_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gare(
    gare_id: int,
    _: User = Depends(require_permission("GARE_DELETE")),
    db: Session = Depends(get_db),
):
    GareService(db).delete_gare(gare_id)

@router.post("/{gare_id}/quais", response_model=QuaiRead, status_code=status.HTTP_201_CREATED)
def add_quai(
    gare_id: int,
    data: QuaiCreate,
    _: User = Depends(require_permission("GARE_UPDATE")),
    db: Session = Depends(get_db),
):
    return GareService(db).add_quai(gare_id, numero=data.numero, nom=data.nom, description=data.description)

@router.post("/{gare_id}/zones", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
def add_zone(
    gare_id: int,
    data: ZoneCreate,
    _: User = Depends(require_permission("GARE_UPDATE")),
    db: Session = Depends(get_db),
):
    return GareService(db).add_zone(gare_id, nom=data.nom, type_zone=data.type_zone, description=data.description)

@router.post("/zones/{zone_id}/emplacements", response_model=EmplacementRead, status_code=status.HTTP_201_CREATED)
def add_emplacement(
    zone_id: int,
    data: EmplacementCreate,
    _: User = Depends(require_permission("GARE_UPDATE")),
    db: Session = Depends(get_db),
):
    return GareService(db).add_emplacement(zone_id, code=data.code, nom=data.nom, type_emplacement=data.type_emplacement, description=data.description)

@router.get("/{gare_id}/quais", response_model=list[QuaiRead])
def list_quais(gare_id: int, _: User = Depends(require_permission("GARE_READ")), db: Session = Depends(get_db)):
    return GareService(db).list_quais(gare_id)

@router.put("/{gare_id}/quais/{quai_id}", response_model=QuaiRead)
def update_quai(gare_id: int, quai_id: int, data: QuaiUpdate, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).update_quai(gare_id, quai_id, **data.model_dump(exclude_unset=True))

@router.patch("/{gare_id}/quais/{quai_id}/toggle", response_model=QuaiRead)
def toggle_quai(gare_id: int, quai_id: int, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).toggle_quai(gare_id, quai_id)

@router.delete("/{gare_id}/quais/{quai_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quai(gare_id: int, quai_id: int, _: User = Depends(require_permission("GARE_DELETE")), db: Session = Depends(get_db)):
    GareService(db).delete_quai(gare_id, quai_id)

@router.get("/{gare_id}/zones", response_model=list[ZoneRead])
def list_zones(gare_id: int, _: User = Depends(require_permission("GARE_READ")), db: Session = Depends(get_db)):
    return GareService(db).list_zones(gare_id)

@router.put("/{gare_id}/zones/{zone_id}", response_model=ZoneRead)
def update_zone(gare_id: int, zone_id: int, data: ZoneUpdate, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).update_zone(gare_id, zone_id, **data.model_dump(exclude_unset=True))

@router.patch("/{gare_id}/zones/{zone_id}/toggle", response_model=ZoneRead)
def toggle_zone(gare_id: int, zone_id: int, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).toggle_zone(gare_id, zone_id)

@router.delete("/{gare_id}/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(gare_id: int, zone_id: int, _: User = Depends(require_permission("GARE_DELETE")), db: Session = Depends(get_db)):
    GareService(db).delete_zone(gare_id, zone_id)

@router.get("/{gare_id}/zones/{zone_id}/emplacements", response_model=list[EmplacementRead])
def list_emplacements(gare_id: int, zone_id: int, _: User = Depends(require_permission("GARE_READ")), db: Session = Depends(get_db)):
    return GareService(db).list_emplacements(gare_id, zone_id)

@router.put("/{gare_id}/zones/{zone_id}/emplacements/{emplacement_id}", response_model=EmplacementRead)
def update_emplacement(gare_id: int, zone_id: int, emplacement_id: int, data: EmplacementUpdate, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).update_emplacement(gare_id, zone_id, emplacement_id, **data.model_dump(exclude_unset=True))

@router.patch("/{gare_id}/zones/{zone_id}/emplacements/{emplacement_id}/toggle", response_model=EmplacementRead)
def toggle_emplacement(gare_id: int, zone_id: int, emplacement_id: int, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).toggle_emplacement(gare_id, zone_id, emplacement_id)

@router.delete("/{gare_id}/zones/{zone_id}/emplacements/{emplacement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emplacement(gare_id: int, zone_id: int, emplacement_id: int, _: User = Depends(require_permission("GARE_DELETE")), db: Session = Depends(get_db)):
    GareService(db).delete_emplacement(gare_id, zone_id, emplacement_id)
