import csv
import io
import secrets
from datetime import date, datetime

from fastapi import APIRouter, Header, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import driver_scope, ensure_depart_access, station_agent_scope, has_permission, resolve_owner_scope, is_staff, get_user_cooperative_ids, get_user_gare_ids, has_active_role, has_global_cooperative_access, ensure_cooperative_access, require_permission, get_optional_current_user
from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.models.depart import Depart
from app.models.place import DepartPlace
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.reservation import CounterSaleCreate, DepartPlaceRead, DepartPlaceStatusUpdate, PublicReservationCreate, PublicReservationCreateRead, ReservationCreate, ReservationRead, ReservationUpdate
from app.services.finance import FinanceService
from app.schemas.finance.schema import PaiementEnLigneRead, PublicPaymentCreate
from app.services.reservation import ReservationService
from app.services.audit import AuditService

router = APIRouter(tags=["reservations"])


def _scope(db: Session, user: User) -> tuple[int | None, set[int] | None]:
    return resolve_owner_scope(db, user)


@router.get("/reservations", response_model=PageResponse[ReservationRead])
def list_reservations(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100), status_filter: str | None = Query(None, alias="statut"),
    date_from: date | None = None, date_to: date | None = None,
    id_cooperative: int | None = Query(None, ge=1),
    id_gare: int | None = Query(None, ge=1),
    id_itineraire: int | None = Query(None, ge=1),
    id_depart: int | None = Query(None, ge=1),
    sort_by: str = Query("created_at", pattern="^(created_at|date_expiration|montant_total|statut|date_depart)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(require_permission("RESERVATION_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return ReservationService(db).list_reservations(
        page=page, page_size=page_size, search=search, statut=status_filter,
        date_from=date_from, date_to=date_to, id_cooperative=id_cooperative,
        id_gare=id_gare, id_itineraire=id_itineraire, id_depart=id_depart,
        sort_by=sort_by, sort_order=sort_order, owner_id=owner_id,
        cooperative_ids=cooperative_ids, chauffeur_id=driver_scope(db, current_user),
        gare_ids=station_agent_scope(db, current_user),
    )


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
        ensure_depart_access(db, current_user, depart)
    return ReservationService(db).list_places(depart_id, include_unavailable=not available_only)


@router.get("/public/departs/{depart_id}/places", response_model=list[DepartPlaceRead], include_in_schema=False)
@router.get("/reservations/public/departs/{depart_id}/places", response_model=list[DepartPlaceRead])
def list_public_depart_places(depart_id: int, db: Session = Depends(get_db)):
    service = ReservationService(db)
    service._get_open_depart(depart_id)
    return service.list_places(depart_id, include_unavailable=True)


@router.post("/reservations/public", response_model=PublicReservationCreateRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_public_reservation(
    request: Request,
    data: PublicReservationCreate,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    service = ReservationService(db)
    reservation, access_token = service.create_public_reservation(
        depart_id=data.id_depart,
        places=[place.model_dump() for place in data.places],
        name=data.nom_reservataire,
        telephone=data.telephone_reservataire,
        email=data.email_reservataire,
        user=current_user,
        command_key=data.cle_idempotence,
    )
    return {"reservation": reservation, "access_token": access_token, "payment": None,
            "acompte_minimum": FinanceService._minimum_deposit(reservation.montant_total, reservation)}


@router.get("/reservations/policy")
def get_booking_policy(db: Session = Depends(get_db)):
    from app.services.booking_policy import booking_policy
    return booking_policy(db)


@router.post("/reservations/public/{reservation_number}/paiement", response_model=PaiementEnLigneRead)
def pay_public_reservation(reservation_number: str, data: PublicPaymentCreate,
                           access_token: str = Header(..., alias="X-Reservation-Token"), db: Session = Depends(get_db)):
    item = ReservationService(db).get_public_reservation(reservation_number, access_token)
    return FinanceService(db).create_papi_payment(reservation_id=item.id, amount=data.montant,
        idempotency_key=data.cle_idempotence, user_id=None, client_name=item.nom_reservataire,
        payer_phone=data.telephone_paiement, payer_email=item.email_reservataire, provider=data.fournisseur)


@router.post("/reservations/public/{reservation_number}/cancel", response_model=ReservationRead)
def cancel_public_reservation(reservation_number: str, access_token: str = Header(..., alias="X-Reservation-Token"), db: Session = Depends(get_db)):
    service = ReservationService(db)
    item = service.get_public_reservation(reservation_number, access_token)
    return service.cancel(item.id, owner_id=item.id_user)


@router.get("/reservations/public/{reservation_number}", response_model=ReservationRead)
def get_public_reservation(reservation_number: str, token: str | None = Query(default=None, min_length=20),
                           access_token: str | None = Header(default=None, alias="X-Reservation-Token"), db: Session = Depends(get_db)):
    if not (access_token or token):
        raise HTTPException(404, "Réservation introuvable.")
    return ReservationService(db).get_public_reservation(reservation_number, access_token or token)


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
    ensure_depart_access(db, current_user, depart)
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
    ensure_depart_access(db, current_user, depart)
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
    if owner_id is None:
        depart = db.get(Depart, data.id_depart)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        ensure_depart_access(db, current_user, depart)
    item = ReservationService(db).create_reservation(user=current_user, depart_id=data.id_depart, places=[place.model_dump() for place in data.places], as_passenger=owner_id is not None)
    AuditService(db).record(user_id=current_user.id, action="RESERVATION_CREEE", entity_type="reservation", entity_id=item.id, after={"statut": item.statut, "montant_total": item.montant_total})
    db.commit()
    return item


@router.post("/reservations/guichet", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def counter_sale(
    data: CounterSaleCreate,
    current_user: User = Depends(require_permission("RESERVATION_CREATE")), db: Session = Depends(get_db),
):
    """Sell seats at the counter in one step: book, confirm, and take cash if a desk is given.

    All database changes are committed together; failures roll back the sale.
    """
    if not is_staff(current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La vente au guichet est réservée au personnel.")
    if data.id_caisse is not None and not has_permission(current_user, "PAIEMENT_PROCESS"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous ne pouvez pas encaisser de paiement.")
    depart = db.get(Depart, data.id_depart)
    if not depart:
        raise HTTPException(404, "Départ introuvable.")
    ensure_depart_access(db, current_user, depart)
    from app.services.reservation.counter_sale import sell_at_counter
    return sell_at_counter(db, user=current_user, depart_id=data.id_depart,
        places=[place.model_dump() for place in data.places], caisse_id=data.id_caisse,
        reference=data.reference_paiement, gare_ids=get_user_gare_ids(db, current_user))


@router.get("/reservations/export.csv")
def export_reservations(
    search: str | None = Query(None, max_length=100), status_filter: str | None = Query(None, alias="statut"),
    date_from: date | None = None, date_to: date | None = None,
    id_cooperative: int | None = Query(None, ge=1),
    id_gare: int | None = Query(None, ge=1),
    id_itineraire: int | None = Query(None, ge=1),
    id_depart: int | None = Query(None, ge=1),
    current_user: User = Depends(require_permission("RESERVATION_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    items = ReservationService(db).list_reservations(
        for_export=True, search=search, statut=status_filter,
        date_from=date_from, date_to=date_to, id_cooperative=id_cooperative,
        id_gare=id_gare, id_itineraire=id_itineraire, id_depart=id_depart,
        sort_by="date_depart", sort_order="asc", owner_id=owner_id,
        cooperative_ids=cooperative_ids, chauffeur_id=driver_scope(db, current_user),
        gare_ids=station_agent_scope(db, current_user),
    )
    from tempfile import TemporaryFile
    from fastapi.responses import StreamingResponse
    from starlette.background import BackgroundTask
    output = TemporaryFile(mode="w+", encoding="utf-8-sig", newline="")
    writer = csv.writer(output)
    writer.writerow(["reservation", "depart", "date_depart", "heure_depart", "places", "montant", "statut"])
    for item in items:
        writer.writerow([
            item.numero_reservation,
            item.id_depart,
            item.depart.date_depart if item.depart else "",
            item.depart.heure_depart if item.depart else "",
            ", ".join(str(place.depart_place.numero_place) for place in item.places if place.depart_place),
            item.montant_total,
            item.statut,
        ])
    output.seek(0)
    return StreamingResponse(iter(lambda: output.read(65536), ""), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=reservations.csv"}, background=BackgroundTask(output.close))


@router.get("/reservations/{reservation_id}", response_model=ReservationRead)
def get_reservation(
    reservation_id: int,
    current_user: User = Depends(require_permission("RESERVATION_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return ReservationService(db)._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=driver_scope(db, current_user), gare_ids=station_agent_scope(db, current_user))


@router.patch("/reservations/{reservation_id}", response_model=ReservationRead)
def update_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    current_user: User = Depends(require_permission("RESERVATION_UPDATE")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    service = ReservationService(db)
    before_item = service._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=driver_scope(db, current_user), gare_ids=station_agent_scope(db, current_user))
    before = {"id_depart": before_item.id_depart, "places": [row.id_depart_place for row in before_item.places]}
    item = service.update_reservation(
        reservation_id,
        depart_id=data.id_depart,
        places=[place.model_dump() for place in data.places],
        owner_id=owner_id,
        cooperative_ids=cooperative_ids, chauffeur_id=driver_scope(db, current_user), gare_ids=station_agent_scope(db, current_user),
        default_passenger_name=f"{current_user.first_name or ''} {current_user.name or ''}".strip(),
    )
    AuditService(db).record(
        user_id=current_user.id,
        action="RESERVATION_MODIFIEE",
        entity_type="reservation",
        entity_id=item.id,
        before=before,
        after={"id_depart": item.id_depart, "places": [row.id_depart_place for row in item.places]},
    )
    db.commit()
    return item


@router.post("/reservations/{reservation_id}/confirm", response_model=ReservationRead)
def confirm_reservation(
    reservation_id: int,
    current_user: User = Depends(require_permission("RESERVATION_UPDATE")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    if owner_id is not None:
        # Seats booked by a passenger are only confirmed once paid.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La réservation sera confirmée lors du paiement.")
    return ReservationService(db).confirm(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=driver_scope(db, current_user), gare_ids=station_agent_scope(db, current_user))


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation(
    reservation_id: int,
    id_caisse: int | None = Query(None),
    current_user: User = Depends(require_permission("RESERVATION_CANCEL")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    can_refund_now = has_permission(current_user, "PAIEMENT_REFUND") and has_permission(current_user, "CAISSE_MANAGE")
    item = ReservationService(db).cancel(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids, chauffeur_id=driver_scope(db, current_user), caisse_id=id_caisse, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user), can_refund_now=can_refund_now)
    AuditService(db).record(user_id=current_user.id, action="RESERVATION_ANNULEE", entity_type="reservation", entity_id=reservation_id, after={"statut": item.statut})
    db.commit()
    return item


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
    ensure_depart_access(db, current_user, depart)
    return ReservationService(db).update_place_status(place_id, data.statut)


@router.get("/reservations/public/{reservation_number}/paiement", response_model=PaiementEnLigneRead | None)
def pending_public_payment(reservation_number: str, access_token: str = Header(..., alias="X-Reservation-Token"), db: Session = Depends(get_db)):
    item = ReservationService(db).get_public_reservation(reservation_number, access_token)
    return FinanceService(db).pending_online_payment(item.id)
