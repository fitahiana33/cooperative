from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_user_cooperative_ids, has_global_cooperative_access, require_permission
from app.db.session import get_db
from app.models.user import User
from app.services.reports import ReportService

router = APIRouter(prefix="/rapports", tags=["reports"])


def _scope(db: Session, user: User) -> set[int] | None:
    return None if has_global_cooperative_access(user) else get_user_cooperative_ids(db, user)


@router.get("")
def report(report_type: str = Query("daily", alias="type"), date_from: date | None = None, date_to: date | None = None, current_user: User = Depends(require_permission("RAPPORT_READ")), db: Session = Depends(get_db)):
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=29))
    return {"type": report_type, "date_from": start, "date_to": end, "rows": ReportService(db).rows(report_type=report_type, date_from=start, date_to=end, cooperative_ids=_scope(db, current_user))}


@router.get("/export.csv", response_class=PlainTextResponse)
def report_csv(report_type: str = Query("daily", alias="type"), date_from: date | None = None, date_to: date | None = None, current_user: User = Depends(require_permission("RAPPORT_READ")), db: Session = Depends(get_db)):
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=29))
    rows = ReportService(db).rows(report_type=report_type, date_from=start, date_to=end, cooperative_ids=_scope(db, current_user))
    return PlainTextResponse(ReportService.csv_text(rows), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="rapport-{report_type}-{start}-{end}.csv"'})


@router.get("/export.pdf", response_class=Response)
def report_pdf(report_type: str = Query("daily", alias="type"), date_from: date | None = None, date_to: date | None = None, current_user: User = Depends(require_permission("RAPPORT_READ")), db: Session = Depends(get_db)):
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=29))
    rows = ReportService(db).rows(report_type=report_type, date_from=start, date_to=end, cooperative_ids=_scope(db, current_user))
    return Response(content=ReportService.pdf_bytes(f"Rapport {report_type} — {start} au {end}", rows), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="rapport-{report_type}-{start}-{end}.pdf"'})
