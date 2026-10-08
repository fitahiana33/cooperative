import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import has_permission, resolve_owner_scope, is_staff, get_user_cooperative_ids, get_user_gare_ids, has_active_role, has_global_cooperative_access, ensure_cooperative_access, require_permission
from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.models.depart import Depart
from app.models.place import DepartPlace
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.reservation import CounterSaleCreate, DepartPlaceRead, DepartPlaceStatusUpdate, ReservationCreate, ReservationRead
from app.services.finance import FinanceService
from app.services.reservation import ReservationService

router = APIRouter(tags=["reservations"])


def _scope(db: Session, user: User) -> tuple[int | None, set[int] | None]:
    return resolve_owner_scope(db, user)


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
    if is_staff(current_user) or not has_active_role(current_user, UserRole.PASSAGER):
        ensure_cooperative_access(db, current_user, depart.id_cooperative)
    return ReservationService(db).list_places(depart_id, include_unavailable=not available_only)


@router.get("/departs/{depart_id}/passagers")
def list_depart_passengers(
    depart_id: int,
    current_user: User = Depends(require_permission("RESERVATION_READ")),
    db: Session = Depends(get_db),
):
    """Passengers of a departure with their boarding status (on-screen manifest)."""
    depart = db.get(Depart, depart_id)
    if not depart:
        raise HTTPException(404, "Départ introuvable.")
    ensure_cooperative_access(db, current_user, depart.id_cooperative)
    return ReservationService(db).manifest_rows(depart_id)


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
@limiter.limit("20/minute")
def create_reservation(
    request: Request,
    data: ReservationCreate,
    current_user: User = Depends(require_permission("RESERVATION_CREATE")), db: Session = Depends(get_db),
):
    owner_id, _ = _scope(db, current_user)
    return ReservationService(db).create_reservation(user=current_user, depart_id=data.id_depart, places=[place.model_dump() for place in data.places], as_passenger=owner_id is not None)


@router.post("/reservations/guichet", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def counter_sale(
    data: CounterSaleCreate,
    current_user: User = Depends(require_permission("RESERVATION_CREATE")), db: Session = Depends(get_db),
):
    """Sell seats at the counter in one step: book, confirm, and take cash if a desk is given.

    If a later step fails, the reservation is cancelled so its seats are not left blocked.
    """
    if not has_permission(current_user, "RESERVATION_UPDATE"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La vente au guichet est réservée au personnel.")
    if data.id_caisse is not None and not has_permission(current_user, "PAIEMENT_PROCESS"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous ne pouvez pas encaisser de paiement.")
    service = ReservationService(db)
    created = service.create_reservation(user=current_user, depart_id=data.id_depart, places=[place.model_dump() for place in data.places])
    try:
        reservation = service.confirm(created.id)
        if data.id_caisse is not None:
            FinanceService(db).create_cash_payment(
                reservation_id=reservation.id, caisse_id=data.id_caisse, amount=reservation.montant_total,
                reference=data.reference_paiement, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user),
            )
    except HTTPException:
        db.rollback()
        service.cancel(created.id, agent_id=current_user.id)
        raise
    return service._get(created.id)


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
    if owner_id is not None:
        # Seats booked by a passenger are only confirmed once paid.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La réservation sera confirmée lors du paiement.")
    return ReservationService(db).confirm(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids)


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation(
    reservation_id: int,
    id_caisse: int | None = Query(None),
    current_user: User = Depends(require_permission("RESERVATION_CANCEL")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    can_refund_now = has_permission(current_user, "PAIEMENT_REFUND") and has_permission(current_user, "CAISSE_MANAGE")
    return ReservationService(db).cancel(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, caisse_id=id_caisse, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user), can_refund_now=can_refund_now)


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
