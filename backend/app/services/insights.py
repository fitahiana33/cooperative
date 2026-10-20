from datetime import date, timedelta
from statistics import mean, pstdev

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.clock import local_today
from app.models.depart import Depart
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.models.itineraire import Itineraire


class DecisionSupportService:
    """Explainable forecasts, deliberately transparent and deterministic.

    This is not a black-box prediction: it uses a weighted rolling average by
    route and weekday, and includes the observations used to form each result.
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze(self, *, date_from: date | None = None, cooperative_ids: set[int] | None = None) -> dict:
        today = date_from or local_today()
        history_start = today - timedelta(days=90)
        statement = (
            select(Depart.id_itineraire, Depart.date_depart, func.count(ReservationPlace.id).label("passagers"), func.avg(Depart.nombre_places).label("capacite"))
            .join(Reservation, Reservation.id_depart == Depart.id, isouter=True)
            .join(ReservationPlace, ReservationPlace.id_reservation == Reservation.id, isouter=True)
            .where(Depart.date_depart.between(history_start, today - timedelta(days=1)), or_(Reservation.id.is_(None), Reservation.statut.in_([ReservationStatus.PAYEE, ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE])))
            .group_by(Depart.id_itineraire, Depart.date_depart)
            .order_by(Depart.id_itineraire, Depart.date_depart)
        )
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        grouped: dict[int, list[dict]] = {}
        for row in self.db.execute(statement):
            grouped.setdefault(row.id_itineraire, []).append({"date": row.date_depart, "passagers": int(row.passagers or 0), "capacite": float(row.capacite or 0)})
        route_ids = list(grouped)
        labels = {}
        if route_ids:
            routes = self.db.scalars(select(Itineraire).where(Itineraire.id.in_(route_ids))).all()
            labels = {route.id: f"{route.destination_depart.nom} → {route.destination_arrivee.nom}" for route in routes}
        forecasts = []
        anomalies = []
        recommendations = []
        for route_id, observations in grouped.items():
            values = [item["passagers"] for item in observations]
            recent = values[-30:] or values
            weighted = sum(value * (index + 1) for index, value in enumerate(recent)) / sum(range(1, len(recent) + 1))
            weekday_values = [item["passagers"] for item in observations if item["date"].isoweekday() == today.isoweekday()]
            seasonal = mean(weekday_values[-8:]) if weekday_values else weighted
            forecast = round((weighted * 0.65) + (seasonal * 0.35), 2)
            capacity = mean([item["capacite"] for item in observations if item["capacite"] > 0] or [1])
            # Project the next 30 calendar days day by day using the observed
            # weekday pattern; do not apply an arbitrary fixed uplift.
            by_weekday = {
                weekday: mean([item["passagers"] for item in observations if item["date"].isoweekday() == weekday][-8:])
                for weekday in range(1, 8)
                if any(item["date"].isoweekday() == weekday for item in observations)
            }
            next_30 = 0.0
            for offset in range(30):
                future_day = today + timedelta(days=offset + 1)
                seasonal_day = by_weekday.get(future_day.isoweekday(), weighted)
                next_30 += (weighted * 0.65) + (seasonal_day * 0.35)
            forecasts.append({"id_itineraire": route_id, "libelle": labels.get(route_id, f"Itinéraire #{route_id}"), "passagers_7_jours": forecast, "passagers_30_jours": round(next_30, 2), "remplissage_7_jours": round(min(100, forecast / capacity * 100), 2), "methode": "moyenne pondérée 30 jours + saisonnalité hebdomadaire projetée jour par jour", "observations": len(observations)})
            deviation = pstdev(values) if len(values) > 1 else 0
            threshold = mean(values) + (2 * deviation)
            for item in observations:
                if deviation and item["passagers"] > threshold:
                    anomalies.append({"id_itineraire": route_id, "libelle": labels.get(route_id, f"Itinéraire #{route_id}"), "date": item["date"], "valeur": item["passagers"], "moyenne": round(mean(values), 2), "z_score": round((item["passagers"] - mean(values)) / deviation, 2), "type": "FORTE_DEMANDE"})
            recommended_departures = max(1, int((forecast / max(capacity * 0.8, 1)) + 0.999))
            recommendations.append({"id_itineraire": route_id, "libelle": labels.get(route_id, f"Itinéraire #{route_id}"), "departs_recommandes": recommended_departures, "raison": f"{forecast:.1f} passagers prévus / départ avec une capacité moyenne de {capacity:.1f} et une cible de remplissage de 80 %"})
        return {"date_reference": today, "periode_observee": {"du": history_start, "au": today - timedelta(days=1)}, "previsions": forecasts, "recommandations": recommendations, "anomalies": anomalies, "limites": "Prévision indicative : elle nécessite un historique suffisant et ne remplace pas la validation du responsable."}
