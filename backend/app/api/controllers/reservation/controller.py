import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_user_cooperative_ids, get_user_gare_ids, has_active_role, has_global_cooperative_access, ensure_cooperative_access, require_permission
from app.db.session import get_db
from app.models.depart import Depart
from app.models.place import DepartPlace
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.reservation import DepartPlaceRead, DepartPlaceStatusUpdate, ReservationCreate, ReservationRead
from app.services.reservation import ReservationService

router = APIRouter(tags=["reservations"])


def _scope(db: Session, user: User) -> tuple[int | None, set[int] | None]:
    if has_global_cooperative_access(user):
        return None, None
    if has_active_role(user, UserRole.PASSAGER):
        return user.id, None
    return None, get_user_cooperative_ids(db, user)


@router.get("/reservations", response_model=PageResponse[ReservationRead])
def list_reservations(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100), status_filter: str | None = Query(None, alias="statut"),
    date_from: date | None = None, date_to: date | None = None,
    sort_by: str = Query("created_at", pattern="^(created_at|date_expiration|montant_total|statut|date_depart)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(require_permission("RESERVATION_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return ReservationService(db).list_reservations(page=page, page_size=page_size, search=search, statut=status_filter, date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order, owner_id=owner_id, cooperative_ids=cooperative_ids)


@router.get("/departs/{depart_id}/places", response_model=list[DepartPlaceRead])
def list_depart_places(
    depart_id: int, available_only: bool = False,
    current_user: User = Depends(require_permission("RESERVATION_READ")), db: Session = Depends(get_db),
):
    depart = db.get(Depart, depart_id)
    if not depart:
        from fastapi import HTTPException
        raise HTTPException(404, "Départ introuvable.")
    if not has_active_role(current_user, UserRole.PASSAGER):
        ensure_cooperative_access(db, current_user, depart.id_cooperative)
    return ReservationService(db).list_places(depart_id, include_unavailable=not available_only)


@router.get("/departs/{depart_id}/manifest.csv")
def export_depart_manifest(
    depart_id: int,
    current_user: User = Depends(require_permission("RESERVATION_READ")),
    db: Session = Depends(get_db),
):
    depart = db.get(Depart, depart_id)
    if not depart:
        from fastapi import HTTPException
        raise HTTPException(404, "Départ introuvable.")
    ensure_cooperative_access(db, current_user, depart.id_cooperative)
    rows = ReservationService(db).manifest_rows(depart_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "reservation", "passager", "telephone", "place", "billet",
        "statut_reservation", "statut_billet", "pointage_embarquement", "date_pointage",
    ])
    for row in rows:
        writer.writerow([
            row["reservation"], row["passager"], row["telephone"], row["place"], row["billet"],
            row["reservation_statut"], row["billet_statut"], row["pointage"], row["date_pointage"],
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=manifeste-depart-{depart_id}.csv"},
    )


@router.post("/reservations", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    data: ReservationCreate,
    current_user: User = Depends(require_permission("RESERVATION_CREATE")), db: Session = Depends(get_db),
):
    return ReservationService(db).create_reservation(user=current_user, depart_id=data.id_depart, places=[place.model_dump() for place in data.places], date_expiration=data.date_expiration)


@router.get("/reservations/export.csv")
def export_reservations(
    search: str | None = Query(None, max_length=100), status_filter: str | None = Query(None, alias="statut"),
    date_from: date | None = None, date_to: date | None = None,
    current_user: User = Depends(require_permission("RESERVATION_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    result = ReservationService(db).list_reservations(page=1, page_size=1000, search=search, statut=status_filter, date_from=date_from, date_to=date_to, sort_by="date_depart", sort_order="asc", owner_id=owner_id, cooperative_ids=cooperative_ids)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["reservation", "depart", "date_depart", "heure_depart", "places", "montant", "statut"])
    for item in result["items"]:
        writer.writerow([
            item.numero_reservation,
            item.id_depart,
            item.depart.date_depart if item.depart else "",
            item.depart.heure_depart if item.depart else "",
            ", ".join(str(place.depart_place.numero_place) for place in item.places if place.depart_place),
            item.montant_total,
            item.statut,
        ])
    return Response(content=output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=reservations.csv"})


@router.get("/reservations/{reservation_id}", response_model=ReservationRead)
def get_reservation(
    reservation_id: int,
    current_user: User = Depends(require_permission("RESERVATION_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return ReservationService(db)._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids)


@router.post("/reservations/{reservation_id}/confirm", response_model=ReservationRead)
def confirm_reservation(
    reservation_id: int,
    current_user: User = Depends(require_permission("RESERVATION_UPDATE")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return ReservationService(db).confirm(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids)


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation(
    reservation_id: int,
    id_caisse: int | None = Query(None),
    current_user: User = Depends(require_permission("RESERVATION_CANCEL")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return ReservationService(db).cancel(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, caisse_id=id_caisse, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user))


@router.patch("/depart-places/{place_id}", response_model=DepartPlaceRead)
def update_depart_place(
    place_id: int, data: DepartPlaceStatusUpdate,
    current_user: User = Depends(require_permission("PLACE_MANAGE")), db: Session = Depends(get_db),
):
    place = db.get(DepartPlace, place_id)
    if not place:
        from fastapi import HTTPException
        raise HTTPException(404, "Place introuvable.")
    depart = db.get(Depart, place.id_depart)
    ensure_cooperative_access(db, current_user, depart.id_cooperative)
    return ReservationService(db).update_place_status(place_id, data.statut)
