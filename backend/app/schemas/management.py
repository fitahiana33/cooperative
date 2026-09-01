from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class RoleCreate(BaseModel):
    libelle: str = Field(min_length=2, max_length=100)
    description: str | None = None
class RoleRead(RoleCreate):
    id: int; is_active: bool; created_at: datetime
    model_config = ConfigDict(from_attributes=True)
class PermissionCreate(BaseModel):
    libelle: str = Field(min_length=2, max_length=100); code: str = Field(min_length=2, max_length=100); module: str = Field(min_length=2, max_length=100); description: str | None = None
class PermissionRead(PermissionCreate):
    id: int; is_active: bool; created_at: datetime
    model_config = ConfigDict(from_attributes=True)
class GareCreate(BaseModel):
    nom: str; adresse: str; ville: str; region: str | None = None; telephone: str | None = None; email: str | None = None; description: str | None = None; latitude: float | None = None; longitude: float | None = None
class GareRead(GareCreate):
    id: int; is_active: bool; created_at: datetime
    model_config = ConfigDict(from_attributes=True)
class QuaiCreate(BaseModel):
    numero: str; nom: str | None = None; description: str | None = None
class ZoneCreate(BaseModel):
    nom: str; type_zone: str | None = None; description: str | None = None
class EmplacementCreate(BaseModel):
    code: str; nom: str | None = None; type_emplacement: str | None = None; description: str | None = None
class CooperativeCreate(BaseModel):
    nom: str; sigle: str | None = None; numero_agrement: str | None = None; adresse: str | None = None; ville: str | None = None; telephone: str | None = None; email: str | None = None; description: str | None = None; responsable_id: int | None = None
class CooperativeRead(CooperativeCreate):
    id: int; is_active: bool; created_at: datetime
    model_config = ConfigDict(from_attributes=True)
class AssociationCreate(BaseModel):
    id_cooperative: int; date_debut: date | None = None; date_fin: date | None = None
class MemberCreate(BaseModel):
    id_user: int; fonction: str | None = None; date_adhesion: date | None = None; date_fin: date | None = None
