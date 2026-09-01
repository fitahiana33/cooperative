from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.schemas.management import (
    RoleCreate, RoleRead, PermissionCreate, PermissionRead,
    GareCreate, GareRead, QuaiCreate, ZoneCreate, EmplacementCreate,
    CooperativeCreate, CooperativeRead, AssociationCreate, MemberCreate
)
from app.schemas.common import PageResponse
from app.services.role.service import RoleService
from app.services.gare.service import GareService
from app.services.cooperative.service import CooperativeService
from app.api.controllers.authentication.dependencies import require_permission, require_admin

router = APIRouter(tags=["management"])

# ================================
# ROLES & PERMISSIONS
# ================================
@router.get("/roles", response_model=PageResponse[RoleRead])
def list_roles(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, sort_by: str = "libelle", sort_order: str = Query("asc", pattern="^(asc|desc)$"), _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    return RoleService(db).list_roles(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(data: RoleCreate, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    return RoleService(db).create_role(libelle=data.libelle, description=data.description)

@router.put("/roles/{role_id}", response_model=RoleRead)
def update_role(role_id: int, data: RoleCreate, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    return RoleService(db).update_role(role_id, **data.model_dump())

@router.patch("/roles/{role_id}/toggle", response_model=RoleRead)
def toggle_role(role_id: int, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    return RoleService(db).toggle_role(role_id)

@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    RoleService(db).delete_role(role_id)

@router.get("/permissions", response_model=PageResponse[PermissionRead])
def list_permissions(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, sort_by: str = "code", sort_order: str = Query("asc", pattern="^(asc|desc)$"), _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    return RoleService(db).list_permissions(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("/permissions", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
def create_permission(data: PermissionCreate, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    return RoleService(db).create_permission(code=data.code, libelle=data.libelle, module=data.module, description=data.description)

@router.put("/permissions/{permission_id}", response_model=PermissionRead)
def update_permission(permission_id: int, data: PermissionCreate, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    return RoleService(db).update_permission(permission_id, **data.model_dump())

@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: int, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    RoleService(db).delete_permission(permission_id)

@router.post("/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_permission(role_id: int, permission_id: int, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    RoleService(db).assign_permission_to_role(role_id, permission_id)

@router.delete("/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_permission(role_id: int, permission_id: int, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    RoleService(db).revoke_permission_from_role(role_id, permission_id)

@router.post("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_role(user_id: int, role_id: int, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    RoleService(db).assign_role_to_user(user_id, role_id)

@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_role(user_id: int, role_id: int, _: User = Depends(require_permission("ROLE_MANAGE")), db: Session = Depends(get_db)):
    RoleService(db).revoke_role_from_user(user_id, role_id)

# ================================
# GARES
# ================================
@router.get("/gares", response_model=PageResponse[GareRead])
def list_gares(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, sort_by: str = "nom", sort_order: str = Query("asc", pattern="^(asc|desc)$"), _: User = Depends(require_permission("GARE_READ")), db: Session = Depends(get_db)):
    return GareService(db).list_gares(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("/gares", response_model=GareRead, status_code=status.HTTP_201_CREATED)
def create_gare(data: GareCreate, _: User = Depends(require_permission("GARE_CREATE")), db: Session = Depends(get_db)):
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

@router.get("/gares/{gare_id}", response_model=GareRead)
def get_gare(gare_id: int, _: User = Depends(require_permission("GARE_READ")), db: Session = Depends(get_db)):
    return GareService(db).get_gare(gare_id)

@router.put("/gares/{gare_id}", response_model=GareRead)
def update_gare(gare_id: int, data: GareCreate, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).update_gare(gare_id, **data.model_dump())

@router.patch("/gares/{gare_id}/toggle", response_model=GareRead)
def toggle_gare(gare_id: int, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).toggle_gare(gare_id)

@router.delete("/gares/{gare_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gare(gare_id: int, _: User = Depends(require_permission("GARE_DELETE")), db: Session = Depends(get_db)):
    GareService(db).delete_gare(gare_id)

@router.post("/gares/{gare_id}/quais", status_code=status.HTTP_201_CREATED)
def add_quai(gare_id: int, data: QuaiCreate, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).add_quai(gare_id, code=data.numero, libelle=data.nom)

@router.post("/gares/{gare_id}/zones", status_code=status.HTTP_201_CREATED)
def add_zone(gare_id: int, data: ZoneCreate, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).add_zone(gare_id, code=data.nom[:3].upper(), nom=data.nom)

@router.post("/zones/{zone_id}/emplacements", status_code=status.HTTP_201_CREATED)
def add_emplacement(zone_id: int, data: EmplacementCreate, _: User = Depends(require_permission("GARE_UPDATE")), db: Session = Depends(get_db)):
    return GareService(db).add_emplacement(zone_id, code=data.code, type_emplacement=data.type_emplacement or "PASSAGER")

# ================================
# COOPERATIVES
# ================================
@router.get("/cooperatives", response_model=PageResponse[CooperativeRead])
def list_cooperatives(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, sort_by: str = "nom", sort_order: str = Query("asc", pattern="^(asc|desc)$"), _: User = Depends(require_permission("COOPERATIVE_READ")), db: Session = Depends(get_db)):
    return CooperativeService(db).list_cooperatives(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("/cooperatives", response_model=CooperativeRead, status_code=status.HTTP_201_CREATED)
def create_cooperative(data: CooperativeCreate, _: User = Depends(require_permission("COOPERATIVE_CREATE")), db: Session = Depends(get_db)):
    return CooperativeService(db).create_cooperative(
        nom=data.nom,
        adresse=data.adresse,
        telephone=data.telephone,
        email=data.email,
        sigle=data.sigle,
        numero_agrement=data.numero_agrement,
        ville=data.ville,
        description=data.description,
        responsable_id=data.responsable_id,
    )

@router.get("/cooperatives/{cooperative_id}", response_model=CooperativeRead)
def get_cooperative(cooperative_id: int, _: User = Depends(require_permission("COOPERATIVE_READ")), db: Session = Depends(get_db)):
    return CooperativeService(db).get_cooperative(cooperative_id)

@router.put("/cooperatives/{cooperative_id}", response_model=CooperativeRead)
def update_cooperative(cooperative_id: int, data: CooperativeCreate, _: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    return CooperativeService(db).update_cooperative(cooperative_id, **data.model_dump())

@router.patch("/cooperatives/{cooperative_id}/toggle", response_model=CooperativeRead)
def toggle_cooperative(cooperative_id: int, _: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    return CooperativeService(db).toggle_cooperative(cooperative_id)

@router.delete("/cooperatives/{cooperative_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cooperative(cooperative_id: int, _: User = Depends(require_permission("COOPERATIVE_DELETE")), db: Session = Depends(get_db)):
    CooperativeService(db).delete_cooperative(cooperative_id)

@router.post("/gares/{gare_id}/cooperatives", status_code=status.HTTP_201_CREATED)
def attach_cooperative(gare_id: int, data: AssociationCreate, _: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    return CooperativeService(db).attach_to_gare(gare_id, data.id_cooperative)

@router.post("/cooperatives/{cooperative_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(cooperative_id: int, data: MemberCreate, _: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    return CooperativeService(db).add_member(cooperative_id, data.id_user, role_cooperative=data.fonction or "MEMBRE")
