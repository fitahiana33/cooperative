from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import require_permission, station_agent_scope, get_user_cooperative_ids, has_global_cooperative_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.common import PageResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=PageResponse[AuditLogRead])
def list_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), action: str | None = None, entity_type: str | None = None, user_id: int | None = None, current_user: User = Depends(require_permission("AUDIT_READ")), db: Session = Depends(get_db)):
    return AuditService(db).list(page=page, page_size=page_size, action=action, entity_type=entity_type, user_id=user_id, gare_ids=station_agent_scope(db, current_user), cooperative_ids=None if has_global_cooperative_access(current_user) or station_agent_scope(db, current_user) is not None else get_user_cooperative_ids(db, current_user))
