"""Append-only incident journal; resolving an incident never changes sold seats."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.depart import Depart
from app.models.user import User
from app.services.audit import AuditService


class DepartureIncidents:
    def __init__(self, db: Session):
        self.db = db

    def list(self, depart_id: int):
        entries = list(self.db.scalars(select(AuditLog).where(AuditLog.entity_type == "depart",
            AuditLog.entity_id == str(depart_id), AuditLog.action.in_(["INCIDENT_SIGNALE", "INCIDENT_RESOLU"]))
            .order_by(AuditLog.id)))
        resolutions = {str(row.after_data["incident_id"]): row for row in entries if row.action == "INCIDENT_RESOLU"}
        actors = {user.id: " ".join(filter(None, [user.first_name, user.name])) for user in self.db.scalars(
            select(User).where(User.id.in_([entry.id_user for entry in entries if entry.id_user])))}
        return [{"id": row.id, "type": row.after_data["type"], "description": row.description,
                 "date": row.created_at, "auteur": actors.get(row.id_user, "Système"),
                 "statut": "RESOLU" if str(row.id) in resolutions else "OUVERT",
                 "resolution": resolutions[str(row.id)].description if str(row.id) in resolutions else None}
                for row in entries if row.action == "INCIDENT_SIGNALE"]

    def report(self, depart_id: int, *, user_id: int, kind: str, description: str):
        self.db.get(Depart, depart_id, with_for_update=True)
        AuditService(self.db).record(user_id=user_id, action="INCIDENT_SIGNALE", entity_type="depart", entity_id=depart_id,
            after={"type": kind}, description=description)
        self.db.commit()
        return self.list(depart_id)

    def resolve(self, depart_id: int, incident_id: int, *, user_id: int, description: str):
        self.db.get(Depart, depart_id, with_for_update=True)
        entry = self.db.get(AuditLog, incident_id)
        if not entry or entry.entity_type != "depart" or entry.entity_id != str(depart_id) or entry.action != "INCIDENT_SIGNALE":
            raise HTTPException(404, "Incident introuvable.")
        if any(row["id"] == incident_id and row["statut"] == "RESOLU" for row in self.list(depart_id)):
            raise HTTPException(409, "Cet incident est déjà résolu.")
        AuditService(self.db).record(user_id=user_id, action="INCIDENT_RESOLU", entity_type="depart", entity_id=depart_id,
            after={"incident_id": incident_id}, description=description)
        self.db.commit()
        return self.list(depart_id)
