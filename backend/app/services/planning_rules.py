"""Shared checks when operational resources or authorizations change."""

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.clock import local_today
from app.models.depart import Depart, DepartStatus


def ensure_planning_covered(db: Session, *, resource: str, starts=None, ends=None, inactive=False, **identifiers) -> None:
    statement = select(Depart.id).where(
        Depart.statut.in_([DepartStatus.PROGRAMME, DepartStatus.EMBARQUEMENT, DepartStatus.RETARDE, DepartStatus.PARTI]),
        or_(Depart.date_depart >= local_today(), Depart.statut == DepartStatus.PARTI),
        *(getattr(Depart, field) == value for field, value in identifiers.items()),
    )
    if not inactive:
        outside = []
        if starts is not None:
            outside.append(Depart.date_depart < starts)
        if ends is not None:
            outside.append(Depart.date_depart > ends)
        if not outside:
            return
        statement = statement.where(or_(*outside))
    if db.scalar(statement.limit(1)) is not None:
        raise HTTPException(409, f"{resource} est utilisé par des départs prévus ou en cours. Réaffectez ou annulez ces départs avant cette modification.")
