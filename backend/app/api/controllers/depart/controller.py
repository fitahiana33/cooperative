from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import (
    has_permission,
    ensure_depart_access,
    is_staff,
    ensure_cooperative_access,
    ensure_gare_access,
    get_user_gare_ids,
    get_user_cooperative_ids,
    has_active_role,
    has_global_cooperative_access,
    require_permission,
)
from app.db.session import get_db
from app.models.depart import Depart, DepartStatus
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.depart import DepartCreate, DepartPointage, DepartRead, DepartStatusUpdate, DepartUpdate, PublicProgrammeRead
from app.schemas.depart.schema import IncidentCreate, IncidentResolution
from app.services.depart import DepartService
from app.services.depart.incidents import DepartureIncidents
from app.services.audit import AuditService

router = APIRouter(prefix="/departs", tags=["departs"])


def _scope(db: Session, user: User) -> set[int] | None:
    if has_global_cooperative_access(user):
        return None
    if is_staff(user):
        return get_user_cooperative_ids(db, user)
    # Passengers browse every departure to book one.
    if has_active_role(user, UserRole.PASSAGER):
        return None
    return set()


def _gare_scope(db: Session, user: User) -> set[int] | None:
    if has_global_cooperative_access(user):
        return None
    if has_active_role(user, UserRole.PASSAGER) and not is_staff(user):
        return None
    return get_user_gare_ids(db, user)


@router.get("", response_model=PageResponse[DepartRead])
def list_departs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("date_depart", pattern="^(date_depart|heure_depart|created_at|statut)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    statut: DepartStatus | None = None,
    id_cooperative: int | None = None,
    id_gare: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    id_destination_depart: int | None = Query(None, description="Ville de départ (destination d'origine)."),
    id_destination_arrivee: int | None = Query(None, description="Ville d'arrivée."),
    id_itineraire: int | None = None,
    id_vehicule: int | None = None,
    id_chauffeur: int | None = None,
    reservable: bool = Query(False, description="Seulement les départs encore réservables (ouverts, non complets, pas encore partis)."),
    current_user: User = Depends(require_permission("DEPART_READ")),
    db: Session = Depends(get_db),
):
    scope = _scope(db, current_user)
    gare_scope = _gare_scope(db, current_user)
    # Filtering only narrows what the user may already see; it needs a check
    # only for scoped staff (passengers browse every departure).
    if id_cooperative is not None and scope is not None:
        ensure_cooperative_access(db, current_user, id_cooperative)
    if id_gare is not None and gare_scope is not None:
        ensure_gare_access(db, current_user, id_gare)
    return DepartService(db).list_departs(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        statut=statut,
        id_cooperative=id_cooperative,
        id_gare=id_gare,
        date_from=date_from,
        date_to=date_to,
        cooperative_ids=scope,
        gare_ids=gare_scope,
        id_destination_depart=id_destination_depart,
        id_destination_arrivee=id_destination_arrivee,
        id_itineraire=id_itineraire,
        id_vehicule=id_vehicule,
        id_chauffeur=id_chauffeur,
        reservable=reservable,
    )


@router.get("/mes-departs", response_model=PageResponse[DepartRead])
def list_my_departs(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    date_from: date | None = None, date_to: date | None = None,
    current_user: User = Depends(require_permission("DEPART_READ")),
    db: Session = Depends(get_db),
):
    return DepartService(db).list_driver_departs(
        current_user.id, page=page, page_size=page_size,
        date_from=date_from, date_to=date_to, sort_by="date_depart", sort_order="asc",
    )


@router.get("/public/programme", response_model=PageResponse[PublicProgrammeRead])
def public_programme(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    date_from: date | None = None,
    date_to: date | None = None,
    id_gare: int | None = None,
    id_cooperative: int | None = None,
    passagers: int = Query(1, ge=1, le=20),
    id_destination_depart: int | None = Query(None, description="Ville de départ."),
    id_destination_arrivee: int | None = Query(None, description="Ville d'arrivée."),
    db: Session = Depends(get_db),
):
    """Catalogue public : aucune connexion n'est nécessaire pour le consulter."""
    return DepartService(db).list_departs(
        page=page,
        page_size=page_size,
        search=search,
        sort_by="date_depart",
        sort_order="asc",
        date_from=date_from,
        date_to=date_to,
        id_gare=id_gare,
        id_cooperative=id_cooperative,
        min_places=passagers,
        id_destination_depart=id_destination_depart,
        id_destination_arrivee=id_destination_arrivee,
        public_programme=True,
    )


@router.get("/public/{depart_id}", response_model=PublicProgrammeRead)
def public_depart(depart_id: int, db: Session = Depends(get_db)):
    catalogue = DepartService(db).list_departs(page=1, page_size=1, id_depart=depart_id, public_programme=True)
    if not catalogue["items"]:
        raise HTTPException(404, "Départ introuvable ou non disponible à la réservation.")
    return catalogue["items"][0]


@router.post("", response_model=DepartRead, status_code=status.HTTP_201_CREATED)
def create_depart(
    data: DepartCreate,
    current_user: User = Depends(require_permission("DEPART_CREATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, data.id_cooperative)
    ensure_gare_access(db, current_user, data.id_gare)
    item = DepartService(db).create_depart(**data.model_dump())
    AuditService(db).record(user_id=current_user.id, action="DEPART_CREE", entity_type="depart", entity_id=item.id, after={"date_depart": item.date_depart, "statut": item.statut})
    db.commit()
    return item


@router.get("/{depart_id}", response_model=DepartRead)
def get_depart(
    depart_id: int,
    current_user: User = Depends(require_permission("DEPART_READ")),
    db: Session = Depends(get_db),
):
    return DepartService(db).get_depart(
        depart_id,
        cooperative_ids=_scope(db, current_user),
        gare_ids=_gare_scope(db, current_user),
    )


@router.put("/{depart_id}", response_model=DepartRead)
def update_depart(
    depart_id: int,
    data: DepartUpdate,
    current_user: User = Depends(require_permission("DEPART_UPDATE")),
    db: Session = Depends(get_db),
):
    service = DepartService(db)
    current = service.get_depart(
        depart_id,
        cooperative_ids=_scope(db, current_user),
        gare_ids=_gare_scope(db, current_user),
    )
    values = data.model_dump(exclude_unset=True)
    ensure_cooperative_access(db, current_user, values.get("id_cooperative", current.id_cooperative))
    next_gare_id = values.get("id_gare", current.id_gare)
    if next_gare_id is not None:
        ensure_gare_access(db, current_user, next_gare_id)
    item = service.update_depart(depart_id, **values)
    AuditService(db).record(user_id=current_user.id, action="DEPART_MODIFIE", entity_type="depart", entity_id=depart_id, after=values)
    db.commit()
    return item


@router.patch("/{depart_id}/status", response_model=DepartRead)
def update_depart_status(
    depart_id: int,
    data: DepartStatusUpdate,
    current_user: User = Depends(require_permission("DEPART_UPDATE")),
    db: Session = Depends(get_db),
):
    service = DepartService(db)
    service.get_depart(
        depart_id,
        cooperative_ids=_scope(db, current_user),
        gare_ids=_gare_scope(db, current_user),
    )
    item = service.update_status(depart_id, data.statut)
    AuditService(db).record(user_id=current_user.id, action="DEPART_STATUT_MODIFIE", entity_type="depart", entity_id=depart_id, after={"statut": data.statut})
    db.commit()
    return item


@router.post("/{depart_id}/pointage", response_model=DepartRead)
def point_depart(
    depart_id: int,
    data: DepartPointage,
    current_user: User = Depends(require_permission("DEPART_POINTAGE")),
    db: Session = Depends(get_db),
):
    return DepartService(db).pointage(depart_id, user_id=current_user.id, pointage_type=data.type)


@router.post("/{depart_id}/cancel", response_model=DepartRead)
def cancel_depart(
    depart_id: int,
    id_caisse: int | None = Query(None),
    current_user: User = Depends(require_permission("DEPART_CANCEL")),
    db: Session = Depends(get_db),
):
    service = DepartService(db)
    service.get_depart(
        depart_id,
        cooperative_ids=_scope(db, current_user),
        gare_ids=_gare_scope(db, current_user),
    )
    can_refund_now = has_permission(current_user, "PAIEMENT_REFUND") and has_permission(current_user, "CAISSE_MANAGE")
    item = service.cancel_depart(depart_id, caisse_id=id_caisse, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user), can_refund_now=can_refund_now)
    AuditService(db).record(user_id=current_user.id, action="DEPART_ANNULE", entity_type="depart", entity_id=depart_id, after={"statut": item.statut})
    db.commit()
    return item


@router.delete("/{depart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_depart(
    depart_id: int,
    current_user: User = Depends(require_permission("DEPART_DELETE")),
    db: Session = Depends(get_db),
):
    service = DepartService(db)
    service.get_depart(
        depart_id,
        cooperative_ids=_scope(db, current_user),
        gare_ids=_gare_scope(db, current_user),
    )
    service.delete_depart(depart_id)


def _incident_depart(db, user, depart_id):
    item = db.get(Depart, depart_id)
    if not item:
        raise HTTPException(404, "Départ introuvable.")
    ensure_depart_access(db, user, item)


@router.get("/{depart_id}/incidents")
def list_incidents(depart_id: int, current_user: User = Depends(require_permission("DEPART_READ")), db: Session = Depends(get_db)):
    _incident_depart(db, current_user, depart_id)
    return DepartureIncidents(db).list(depart_id)


@router.post("/{depart_id}/incidents", status_code=201)
def report_incident(depart_id: int, data: IncidentCreate, current_user: User = Depends(require_permission("DEPART_UPDATE")), db: Session = Depends(get_db)):
    _incident_depart(db, current_user, depart_id)
    return DepartureIncidents(db).report(depart_id, user_id=current_user.id, kind=data.type, description=data.description)


@router.post("/{depart_id}/incidents/{incident_id}/resolution")
def resolve_incident(depart_id: int, incident_id: int, data: IncidentResolution, current_user: User = Depends(require_permission("DEPART_UPDATE")), db: Session = Depends(get_db)):
    _incident_depart(db, current_user, depart_id)
    return DepartureIncidents(db).resolve(depart_id, incident_id, user_id=current_user.id, description=data.description)
