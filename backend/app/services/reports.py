import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet
from app.models.cooperative import Cooperative
from app.models.depart import Depart
from app.models.embarquement import Embarquement
from app.models.finance import OperationCaisse, OperationType, Paiement, PaiementStatus
from app.models.itineraire import Itineraire
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus


class ReportService:
    def __init__(self, db: Session):
        self.db = db

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
        scope = lambda statement: statement.where(Depart.id_cooperative.in_(cooperative_ids)) if cooperative_ids is not None else statement
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
            statement = select(Paiement, Reservation.numero_reservation).join(Reservation).join(Depart, Depart.id == Reservation.id_depart).where(Depart.date_depart.between(date_from, date_to), Paiement.statut == PaiementStatus.VALIDE)
            if cooperative_ids is not None:
                statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
            return [{"reservation": row.numero_reservation, "date": row.Paiement.date_paiement, "montant": row.Paiement.montant, "methode": "Espèces" if str(row.Paiement.methode) == "ESPECES" else str(row.Paiement.methode), "reference": row.Paiement.reference_paiement, "fournisseur": row.Paiement.fournisseur or ""} for row in self.db.execute(statement.order_by(Paiement.date_paiement))]
        if report_type in {"cooperatives", "destinations"}:
            group_column = Depart.id_cooperative if report_type == "cooperatives" else Depart.id_itineraire
            statement = scope(select(group_column.label("groupe"), func.count(Reservation.id).label("reservations"), func.sum(Reservation.montant_total).label("montant")).join(Reservation, Reservation.id_depart == Depart.id).where(Depart.date_depart.between(date_from, date_to), Reservation.statut.not_in([ReservationStatus.ANNULEE, ReservationStatus.EXPIREE])).group_by(group_column).order_by(func.count(Reservation.id).desc()))
            grouped_rows = self.db.execute(statement).all()
            if report_type == "cooperatives":
                labels = dict(self.db.execute(select(Cooperative.id, Cooperative.nom)).all())
                field_name = "cooperative"
            else:
                routes = self.db.scalars(select(Itineraire).where(Itineraire.id.in_([row.groupe for row in grouped_rows])).options(selectinload(Itineraire.destination_depart), selectinload(Itineraire.destination_arrivee))).all()
                labels = {route.id: self._route_label(route) for route in routes}
                field_name = "itineraire"
            return [{field_name: labels.get(row.groupe, "Libellé non renseigné"), "reservations": row.reservations, "montant": row.montant or Decimal("0")} for row in grouped_rows]
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
        """Render a dependency-free, printable PDF with the report rows."""
        import unicodedata

        def safe(value: object) -> str:
            text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
            return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:180]

        keys = list(rows[0].keys()) if rows else []
        lines = [title, " | ".join(keys) if keys else "Aucune donnee pour cette periode."]
        lines.extend(" | ".join(safe(row.get(key, "")) for key in keys) for row in rows[:55])
        stream_lines = ["BT", "/F1 8 Tf", "40 800 Td"]
        for index, line in enumerate(lines):
            if index:
                stream_lines.append("0 -13 Td")
            stream_lines.append(f"({safe(line)}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("ascii")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for number, obj in enumerate(objects, start=1):
            offsets.append(len(pdf)); pdf.extend(f"{number} 0 obj\n".encode()); pdf.extend(obj); pdf.extend(b"\nendobj\n")
        xref = len(pdf); pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
        for offset in offsets[1:]: pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
        return bytes(pdf)
