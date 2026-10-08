from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import (
    ensure_gare_access,
    get_user_cooperative_ids,
    get_user_gare_ids,
    has_global_cooperative_access,
    require_permission,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.finance import CaisseClose, CaisseOpen, CaisseRead, OperationCreate, OperationRead, PaiementCreate, PaiementRead
from app.services.finance import FinanceService

router = APIRouter(tags=["finance"])


@router.get("/caisses", response_model=PageResponse[CaisseRead])
def list_caisses(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), id_gare: int | None = None,
    current_user: User = Depends(require_permission("CAISSE_READ")), db: Session = Depends(get_db),
):
    gare_ids = get_user_gare_ids(db, current_user)
    if id_gare is not None:
        ensure_gare_access(db, current_user, id_gare)
    return FinanceService(db).list_caisses(page=page, page_size=page_size, id_gare=id_gare, gare_ids=gare_ids)


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
        user_id=current_user.id, is_manager=has_global_cooperative_access(current_user),
    )


@router.post("/caisses/{caisse_id}/operations", response_model=OperationRead, status_code=status.HTTP_201_CREATED)
def create_operation(caisse_id: int, data: OperationCreate, current_user: User = Depends(require_permission("CAISSE_MANAGE")), db: Session = Depends(get_db)):
    return FinanceService(db).add_operation(caisse_id, type_operation=data.type_operation, montant=data.montant, id_cooperative=data.id_cooperative, description=data.description, gare_ids=get_user_gare_ids(db, current_user))


@router.get("/paiements", response_model=PageResponse[PaiementRead])
def list_payments(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), id_reservation: int | None = None,
    a_rembourser: bool = Query(False, description="Seulement les paiements à rembourser par un caissier."),
    current_user: User = Depends(require_permission("PAIEMENT_READ")), db: Session = Depends(get_db),
):
    cooperative_ids = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return FinanceService(db).list_payments(page=page, page_size=page_size, reservation_id=id_reservation, cooperative_ids=cooperative_ids, to_refund=a_rembourser)


@router.post("/paiements", response_model=PaiementRead, status_code=status.HTTP_201_CREATED)
def create_payment(data: PaiementCreate, current_user: User = Depends(require_permission("PAIEMENT_PROCESS")), db: Session = Depends(get_db)):
    return FinanceService(db).create_cash_payment(reservation_id=data.id_reservation, caisse_id=data.id_caisse, amount=data.montant, reference=data.reference_paiement, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user))


@router.post("/paiements/{payment_id}/rembourser", response_model=PaiementRead)
def refund_payment(payment_id: int, id_caisse: int = Query(...), current_user: User = Depends(require_permission("PAIEMENT_REFUND")), db: Session = Depends(get_db)):
    return FinanceService(db).refund(payment_id, caisse_id=id_caisse, agent_id=current_user.id, gare_ids=get_user_gare_ids(db, current_user))
