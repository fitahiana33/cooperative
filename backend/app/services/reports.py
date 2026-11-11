import csv
import io
from datetime import date, time, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet
from app.models.cooperative import Cooperative
from app.models.depart import Depart
from app.models.embarquement import Embarquement
from app.models.finance import OperationCaisse, OperationType, Paiement, PaiementStatus
from app.models.itineraire import Itineraire
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.core.clock import local_moment


class ReportService:
    REVENUE_RESERVATION_STATUSES = {
        ReservationStatus.PAYEE,
        ReservationStatus.EMBARQUEE,
        ReservationStatus.TERMINEE,
    }
    def __init__(self, db: Session, *, gare_ids: set[int] | None = None):
        self.db = db
        self.gare_ids = gare_ids

    @staticmethod
    def _route_label(route: Itineraire | None) -> str:
        if not route or not route.destination_depart or not route.destination_arrivee:
            return "Itinéraire non renseigné"
        return f"{route.destination_depart.nom} → {route.destination_arrivee.nom}"

    @staticmethod
    def _status_label(value: object) -> str:
        return {
            "EN_ATTENTE": "En attente", "CONFIRMEE": "Confirmée", "PAYEE": "Payée",
            "ANNULEE": "Annulée", "ANNULE": "Annulé", "EXPIREE": "Expirée", "EMBARQUEE": "Embarquée",
            "TERMINEE": "Terminée", "TERMINE": "Terminé", "PROGRAMME": "Programmé", "EMBARQUEMENT": "Embarquement",
            "RETARDE": "Retardé", "PARTI": "Parti", "VALIDE": "Validé", "REFUSE": "Refusé", "REMBOURSE": "Remboursé",
        }.get(str(value), str(value))

    def rows(self, *, report_type: str, date_from: date, date_to: date, cooperative_ids: set[int] | None = None) -> list[dict]:
        if date_to < date_from or (date_to - date_from).days > 366:
            raise HTTPException(422, "La période doit être valide et ne pas dépasser 366 jours.")
        def scope(statement):
            if cooperative_ids is not None:
                statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
            if self.gare_ids is not None:
                statement = statement.where(Depart.id_gare.in_(self.gare_ids))
            return statement
        if report_type in {"departs", "daily"}:
            statement = scope(select(Depart, Cooperative.nom.label("cooperative"), Itineraire).join(Cooperative, Cooperative.id == Depart.id_cooperative).join(Itineraire, Itineraire.id == Depart.id_itineraire).options(selectinload(Itineraire.destination_depart), selectinload(Itineraire.destination_arrivee)).where(Depart.date_depart.between(date_from, date_to)).order_by(Depart.date_depart, Depart.heure_depart))
            return [{"date": row.Depart.date_depart, "heure": row.Depart.heure_depart, "statut": self._status_label(row.Depart.statut), "cooperative": row.cooperative, "itineraire": self._route_label(row.Itineraire), "places_reservees": row.Depart.places_reservees, "capacite": row.Depart.nombre_places} for row in self.db.execute(statement)]
        if report_type == "reservations":
            statement = scope(select(Reservation, Depart.date_depart, Itineraire).join(Depart, Depart.id == Reservation.id_depart).join(Itineraire, Itineraire.id == Depart.id_itineraire).options(selectinload(Itineraire.destination_depart), selectinload(Itineraire.destination_arrivee)).where(Depart.date_depart.between(date_from, date_to)).order_by(Depart.date_depart, Reservation.created_at))
            return [{"reservation": row.Reservation.numero_reservation, "date": row.date_depart, "itineraire": self._route_label(row.Itineraire), "statut": self._status_label(row.Reservation.statut), "montant": row.Reservation.montant_total} for row in self.db.execute(statement)]
        if report_type == "boarding":
            statement = scope(
                select(Embarquement, Billet.numero_billet, Reservation.numero_reservation, ReservationPlace.nom_passager, Depart.date_depart)
                .join(Billet, Billet.id == Embarquement.id_billet)
                .join(ReservationPlace, ReservationPlace.id == Billet.id_reservation_place)
                .join(Reservation, Reservation.id == ReservationPlace.id_reservation)
                .join(Depart, Depart.id == Reservation.id_depart)
                .where(Depart.date_depart.between(date_from, date_to))
            )
            return [{"billet": row.numero_billet, "reservation": row.numero_reservation, "passager": row.nom_passager, "date_depart": row.date_depart, "statut": self._status_label(row.Embarquement.statut), "date_embarquement": row.Embarquement.date_heure_embarquement} for row in self.db.execute(statement)]
        if report_type in {"financial", "finance"}:
            # Financial periods follow the collection date, not the planned
            # date of the journey. Convert local station days to UTC bounds.
            start = local_moment(date_from, time.min).astimezone(timezone.utc)
            end = local_moment(date_to + timedelta(days=1), time.min).astimezone(timezone.utc)
            collected_at = func.coalesce(Paiement.date_validation, Paiement.date_paiement)
            statement = scope(select(Paiement, Reservation.numero_reservation).join(Reservation)
                .join(Depart, Depart.id == Reservation.id_depart).where(
                    Paiement.statut.in_([PaiementStatus.VALIDE, PaiementStatus.REMBOURSE]),
                    or_((collected_at >= start) & (collected_at < end),
                        (Paiement.date_remboursement >= start) & (Paiement.date_remboursement < end))))
            entries = []
            for payment, number in self.db.execute(statement):
                date = payment.date_validation or payment.date_paiement
                if start <= date < end:
                    entries.append({"reservation": number, "date": date, "operation": "ENCAISSEMENT", "montant": payment.montant,
                        "methode": payment.methode, "reference": payment.reference_paiement, "fournisseur": payment.fournisseur or ""})
                if payment.date_remboursement and start <= payment.date_remboursement < end:
                    entries.append({"reservation": number, "date": payment.date_remboursement, "operation": "REMBOURSEMENT", "montant": -payment.montant,
                        "methode": payment.methode_remboursement, "reference": payment.reference_remboursement, "fournisseur": payment.fournisseur or ""})
            return sorted(entries, key=lambda row: row["date"])
        if report_type in {"cooperatives", "destinations"}:
            group_column = Depart.id_cooperative if report_type == "cooperatives" else Depart.id_itineraire
            paid_reservations = (
                select(
                    Reservation.id.label("reservation_id"),
                    Reservation.id_depart.label("depart_id"),
                    Reservation.montant_total.label("montant_total"),
                    func.count(ReservationPlace.id).label("passagers"),
                )
                .join(ReservationPlace, ReservationPlace.id_reservation == Reservation.id)
                .where(Reservation.statut.in_(self.REVENUE_RESERVATION_STATUSES))
                .group_by(Reservation.id, Reservation.id_depart, Reservation.montant_total)
                .subquery()
            )
            statement = scope(
                select(
                    group_column.label("groupe"),
                    func.count(func.distinct(paid_reservations.c.reservation_id)).label("reservations"),
                    func.sum(paid_reservations.c.passagers).label("passagers"),
                    func.sum(paid_reservations.c.montant_total).label("montant"),
                )
                .join(paid_reservations, paid_reservations.c.depart_id == Depart.id)
                .where(Depart.date_depart.between(date_from, date_to))
                .group_by(group_column)
                .order_by(func.count(func.distinct(paid_reservations.c.reservation_id)).desc())
            )
            grouped_rows = self.db.execute(statement).all()
            if report_type == "cooperatives":
                labels = dict(self.db.execute(select(Cooperative.id, Cooperative.nom)).all())
                field_name = "cooperative"
            else:
                routes = self.db.scalars(select(Itineraire).where(Itineraire.id.in_([row.groupe for row in grouped_rows])).options(selectinload(Itineraire.destination_depart), selectinload(Itineraire.destination_arrivee))).all()
                labels = {route.id: self._route_label(route) for route in routes}
                field_name = "itineraire"
            return [{field_name: labels.get(row.groupe, "Libellé non renseigné"), "reservations": row.reservations, "passagers": row.passagers, "montant": row.montant or Decimal("0")} for row in grouped_rows]
        raise HTTPException(422, "Type de rapport inconnu.")

    @staticmethod
    def csv_text(rows: list[dict]) -> str:
        if not rows:
            return ""
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    @staticmethod
    def pdf_bytes(title: str, rows: list[dict]) -> bytes:
        from app.services.report_pdf import table_pdf
        return table_pdf(title, rows)
