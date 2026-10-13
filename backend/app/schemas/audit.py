from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: int
    id_user: int | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    before_data: dict | None = None
    after_data: dict | None = None
    description: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
