import json

from fastapi import APIRouter, Body, HTTPException, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import (
    ensure_gare_access,
    get_user_cooperative_ids,
    get_user_gare_ids,
    has_global_cooperative_access,
    require_permission,
    station_agent_scope, has_active_role,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.finance import CaisseClose, CaisseOpen, CaisseRead, OperationCreate, OperationRead, PaiementCreate, PaiementEnLigneCreate, PaiementEnLigneRead, PaiementRead
from app.services.finance import FinanceService
from app.schemas.finance.schema import PaymentVerification, RefundCreate

router = APIRouter(tags=["finance"])


@router.post("/paiements/en-ligne", response_model=PaiementEnLigneRead, status_code=status.HTTP_201_CREATED)
def create_online_payment(data: PaiementEnLigneCreate, current_user: User = Depends(require_permission("PAIEMENT_ONLINE")), db: Session = Depends(get_db)):
    return FinanceService(db).create_online_payment(reservation_id=data.id_reservation, amount=data.montant, idempotency_key=data.cle_idempotence, user_id=current_user.id, provider=data.fournisseur, payer_phone=data.telephone_paiement)


@router.post("/paiements/webhooks/{provider}")
async def payment_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        from fastapi import HTTPException
        raise HTTPException(400, "Corps de notification invalide.") from exc
    return FinanceService(db).handle_online_webhook(
        provider=provider,
        payload=payload,
        signature=request.headers.get("X-Papi-Signature"),
        raw_body=raw_body,
    )


@router.get("/caisses", response_model=PageResponse[CaisseRead])
def list_caisses(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), id_gare: int | None = None,
    sort_by: str = Query("date_ouverture", pattern="^(date_ouverture|statut|montant_ouverture)$"), sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(require_permission("CAISSE_READ")), db: Session = Depends(get_db),
):
    gare_ids = get_user_gare_ids(db, current_user)
    if id_gare is not None:
        ensure_gare_access(db, current_user, id_gare)
    return FinanceService(db).list_caisses(page=page, page_size=page_size, id_gare=id_gare, gare_ids=gare_ids, sort_by=sort_by, sort_order=sort_order)


@router.get("/caisses/{caisse_id}", response_model=CaisseRead)
def get_caisse(
    caisse_id: int,
    current_user: User = Depends(require_permission("CAISSE_READ")), db: Session = Depends(get_db),
):
    return FinanceService(db).get_caisse(caisse_id, gare_ids=get_user_gare_ids(db, current_user))


@router.get("/caisses/{caisse_id}/operations", response_model=PageResponse[OperationRead])
def list_caisse_operations(
    caisse_id: int,
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_permission("CAISSE_READ")), db: Session = Depends(get_db),
):
    return FinanceService(db).list_operations(caisse_id, page=page, page_size=page_size, gare_ids=get_user_gare_ids(db, current_user))


@router.post("/caisses", response_model=CaisseRead, status_code=status.HTTP_201_CREATED)
def open_caisse(data: CaisseOpen, current_user: User = Depends(require_permission("CAISSE_OPEN")), db: Session = Depends(get_db)):
    ensure_gare_access(db, current_user, data.id_gare)
    return FinanceService(db).open_caisse(gare_id=data.id_gare, agent_id=current_user.id, montant_ouverture=data.montant_ouverture)


@router.post("/caisses/{caisse_id}/cloturer", response_model=CaisseRead)
def close_caisse(caisse_id: int, data: CaisseClose, current_user: User = Depends(require_permission("CAISSE_CLOSE")), db: Session = Depends(get_db)):
    return FinanceService(db).close_caisse(
        caisse_id, montant_cloture=data.montant_cloture, gare_ids=get_user_gare_ids(db, current_user),
        user_id=current_user.id, is_manager=has_global_cooperative_access(current_user) or has_active_role(current_user, UserRole.RESPONSABLE_GARE),
    )


@router.post("/caisses/{caisse_id}/operations", response_model=OperationRead, status_code=status.HTTP_201_CREATED)
def create_operation(caisse_id: int, data: OperationCreate, current_user: User = Depends(require_permission("CAISSE_MANAGE")), db: Session = Depends(get_db)):
    return FinanceService(db).add_operation(caisse_id, type_operation=data.type_operation, montant=data.montant, id_cooperative=data.id_cooperative, description=data.description, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user))


@router.get("/paiements", response_model=PageResponse[PaiementRead])
def list_payments(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), id_reservation: int | None = None,
    a_verifier: bool = Query(False),
    a_rembourser: bool = Query(False, description="Seulement les paiements à rembourser par un caissier."),
    search: str | None = Query(None, max_length=100), sort_by: str = Query("date_paiement", pattern="^(date_paiement|statut|montant)$"), sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(require_permission("PAIEMENT_READ")), db: Session = Depends(get_db),
):
    cooperative_ids = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return FinanceService(db).list_payments(page=page, page_size=page_size, reservation_id=id_reservation, cooperative_ids=cooperative_ids, gare_ids=station_agent_scope(db, current_user), to_verify=a_verifier, to_refund=a_rembourser, search=search, sort_by=sort_by, sort_order=sort_order)


@router.post("/paiements", response_model=PaiementRead, status_code=status.HTTP_201_CREATED)
def create_payment(data: PaiementCreate, current_user: User = Depends(require_permission("PAIEMENT_PROCESS")), db: Session = Depends(get_db)):
    return FinanceService(db).create_cash_payment(reservation_id=data.id_reservation, caisse_id=data.id_caisse, amount=data.montant, reference=data.reference_paiement, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user))


@router.post("/paiements/{payment_id}/rembourser", response_model=PaiementRead)
def refund_payment(payment_id: int, data: RefundCreate | None = Body(default=None), id_caisse: int | None = Query(default=None), current_user: User = Depends(require_permission("PAIEMENT_REFUND")), db: Session = Depends(get_db)):
    return FinanceService(db).refund(payment_id, caisse_id=id_caisse, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user), method=data.methode if data else "ESPECES", refund_reference=data.reference if data else None)


@router.post("/paiements/{payment_id}/verification-echec", response_model=PaiementRead)
def verify_payment_failure(payment_id: int, data: PaymentVerification,
                           current_user: User = Depends(require_permission("PAIEMENT_REFUND")), db: Session = Depends(get_db)):
    if not any(has_active_role(current_user, role) for role in (UserRole.ADMIN, UserRole.RESPONSABLE_GARE)):
        raise HTTPException(403, "La vérification du prestataire est réservée au responsable de gare.")
    return FinanceService(db).confirm_provider_failure(payment_id, agent_id=current_user.id,
        reference=data.reference_verification, gare_ids=get_user_gare_ids(db, current_user))


@router.get("/paiements/en-cours/{reservation_id}", response_model=PaiementEnLigneRead | None)
def pending_online_payment(reservation_id: int, current_user: User = Depends(require_permission("PAIEMENT_ONLINE")), db: Session = Depends(get_db)):
    return FinanceService(db).pending_online_payment(reservation_id, user_id=current_user.id)
