"""Explainable indicators of observed bookings; no automatic planning decisions."""

from collections import defaultdict
from datetime import date, timedelta
from math import ceil
from statistics import mean, pstdev

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.clock import local_today, local_date, local_timezone
from app.models.depart import Depart, DepartStatus
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.models.itineraire import Itineraire
from app.models.cooperative import Cooperative
from app.models.gare import Gare
from app.models.finance import Paiement, PaiementStatus


def project_passengers(
    reference: date, weighted_daily: float, weekdays: dict[int, float], days: int
) -> float:
    return sum(
        weighted_daily * 0.65
        + weekdays.get((reference + timedelta(days=i)).isoweekday(), weighted_daily)
        * 0.35
        for i in range(1, days + 1)
    )


def forecast_history(reference: date, observations: list[dict]) -> dict:
    """Calendar-day activity including days without service; not unconstrained demand."""
    if not observations:
        recommendations.sort(
            key=lambda item: (-item["departs_recommandes"], item["libelle"])
        )
        actionable = [
            {
                "type": "CAPACITE_A_ETUDIER",
                "priorite": "HAUTE" if item["departs_recommandes"] >= 3 else "NORMALE",
                "libelle": item["libelle"],
                "cooperative": item["cooperative"],
                "gare": item["gare"],
                "id_itineraire": item["id_itineraire"],
                "id_cooperative": item["id_cooperative"],
                "id_gare": item["id_gare"],
                "valeur": item["departs_recommandes"],
                "message": (
                    f"Étudier {item['departs_recommandes']} départ(s) ou une réaffectation "
                    "de capacité sur les 7 prochains jours."
                ),
            }
            for item in recommendations
            if item["departs_recommandes"] > 0
        ]
        actionable.extend(
            {
                "type": "VERIFICATION_REQUISE",
                "priorite": "NORMALE",
                "libelle": item["libelle"],
                "cooperative": item.get("cooperative", ""),
                "gare": item.get("gare", ""),
                "id_itineraire": item["id_itineraire"],
                "id_cooperative": item["id_cooperative"],
                "id_gare": item["id_gare"],
                "valeur": item["valeur"],
                "message": item["raison"],
            }
            for item in anomalies
        )
        priorities = sorted(
            actionable,
            key=lambda item: (
                item["priorite"] != "HAUTE",
                item["type"] != "CAPACITE_A_ETUDIER",
                -float(item["valeur"]),
            ),
        )[:5]
        return {
            "qualite": "INSUFFISANT",
            "observations": 0,
            "raison_qualite": "Aucun départ observé.",
        }
    dates = sorted({r["date"] for r in observations})
    recent_dates = [d for d in dates if d >= reference - timedelta(days=30)]
    fresh = (reference - dates[-1]).days <= 14
    enough = len(recent_dates) >= 14 and (dates[-1] - dates[0]).days >= 27 and fresh
    result = {
        "qualite": "EXPLOITABLE" if enough else "INSUFFISANT",
        "observations": len(dates),
        "jours_actifs_30": len(recent_dates),
        "dernier_depart": dates[-1],
        "raison_qualite": (
            "Au moins 14 jours de service sur les 30 derniers jours et 28 jours de recul."
            if enough
            else "Il faut 14 jours de service sur les 30 derniers jours, 28 jours de recul et une activité datant de 14 jours au plus."
        ),
    }
    if not enough:
        return result
    daily = defaultdict(int)
    for row in observations:
        daily[row["date"]] += row["passagers"]
    recent = [daily[reference - timedelta(days=30 - i)] for i in range(30)]
    weighted = sum(v * (i + 1) for i, v in enumerate(recent)) / 465
    calendar = [
        dates[0] + timedelta(days=i) for i in range((reference - dates[0]).days)
    ]
    weekdays = {
        w: mean([daily[d] for d in calendar if d.isoweekday() == w][-8:])
        for w in range(1, 8)
    }
    result.update(
        passagers_7_jours=round(
            project_passengers(reference, weighted, weekdays, 7), 1
        ),
        passagers_30_jours=round(
            project_passengers(reference, weighted, weekdays, 30), 1
        ),
        jours=[
            {
                "date": reference + timedelta(days=i),
                "passagers": round(
                    project_passengers(
                        reference + timedelta(days=i - 1), weighted, weekdays, 1
                    ),
                    1,
                ),
            }
            for i in range(1, 8)
        ],
    )
    return result


def planning_suggestions(
    days: list[dict], planned: list, capacity: float
) -> list[dict]:
    """Compare the same dates, excluding blocked seats and respecting retained seats."""
    suggestions = []
    for day in days:
        departures = [p for p in planned if p.date_depart == day["date"]]
        offered = sum(p.nombre_places - (p.places_bloquees or 0) for p in departures)
        # Reservations already retained are a lower bound even if the forecast is smaller.
        demand = max(day["passagers"], sum(p.places_reservees for p in departures))
        shortage = max(0, demand - offered * 0.8)
        suggestions.append(
            {
                **day,
                "departs_planifies": len(departures),
                "places_planifiees": offered,
                "places_retenues": sum(p.places_reservees for p in departures),
                "departs_supplementaires": ceil(shortage / max(1, capacity * 0.8)),
            }
        )
    return suggestions


class DecisionSupportService:
    def __init__(self, db: Session, *, gare_ids: set[int] | None = None):
        self.db = db
        self.gare_ids = gare_ids

    def _scope(self, statement, cooperative_ids):
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        if self.gare_ids is not None:
            statement = statement.where(Depart.id_gare.in_(self.gare_ids))
        return statement

    def analyze(
        self, *, date_from: date | None = None, cooperative_ids: set[int] | None = None
    ) -> dict:
        reference = date_from or local_today()
        start = reference - timedelta(days=90)
        # Confirmed deposits retain seats too. Pending/expired/cancelled bookings are excluded.
        sold = [
            ReservationStatus.CONFIRMEE,
            ReservationStatus.PAYEE,
            ReservationStatus.EMBARQUEE,
            ReservationStatus.TERMINEE,
        ]
        query = select(
            Depart.id_itineraire,
            Depart.id_cooperative,
            Depart.id_gare,
            Depart.date_depart,
            Depart.heure_depart,
            Depart.nombre_places,
            func.count(ReservationPlace.id).label("passagers"),
        )
        query = query.join(
            Reservation,
            and_(Reservation.id_depart == Depart.id, Reservation.statut.in_(sold)),
            isouter=True,
        )
        query = query.join(
            ReservationPlace,
            ReservationPlace.id_reservation == Reservation.id,
            isouter=True,
        )
        query = query.where(
            Depart.date_depart.between(start, reference - timedelta(days=1)),
            Depart.statut != DepartStatus.ANNULE,
        )
        query = self._scope(query, cooperative_ids).group_by(Depart.id)
        grouped = defaultdict(list)
        for row in self.db.execute(query):
            grouped[(row.id_itineraire, row.id_cooperative, row.id_gare)].append(
                {
                    "date": row.date_depart,
                    "heure": row.heure_depart.strftime("%H:%M"),
                    "capacite": row.nombre_places,
                    "passagers": row.passagers,
                }
            )
        planned = defaultdict(list)
        query = select(Depart).where(
            Depart.date_depart.between(
                reference + timedelta(days=1), reference + timedelta(days=7)
            ),
            Depart.statut.in_(
                [
                    DepartStatus.PROGRAMME,
                    DepartStatus.RETARDE,
                    DepartStatus.EMBARQUEMENT,
                ]
            ),
        )
        for row in self.db.scalars(self._scope(query, cooperative_ids)):
            key = (row.id_itineraire, row.id_cooperative, row.id_gare)
            planned[key].append(row)
            grouped.setdefault(key, [])
        labels = {
            r.id: f"{r.destination_depart.nom} → {r.destination_arrivee.nom}"
            for r in self.db.scalars(
                select(Itineraire).where(Itineraire.id.in_({k[0] for k in grouped}))
            )
        }
        cooperatives = {
            r.id: r.nom
            for r in self.db.scalars(
                select(Cooperative).where(Cooperative.id.in_({k[1] for k in grouped}))
            )
        }
        stations = {
            r.id: r.nom
            for r in self.db.scalars(
                select(Gare).where(
                    Gare.id.in_({k[2] for k in grouped if k[2] is not None})
                )
            )
        }
        forecasts, recommendations, anomalies, popular = [], [], [], []
        for key, rows in sorted(
            grouped.items(), key=lambda item: (item[0][0], item[0][1], item[0][2] or 0)
        ):
            route, coop, station = key
            identity = {
                "id_itineraire": route,
                "id_cooperative": coop,
                "id_gare": station,
                "libelle": labels[route],
                "cooperative": cooperatives.get(coop, str(coop)),
                "gare": stations.get(station, "Gare non renseignée"),
            }
            model = forecast_history(reference, rows)
            result = {
                **identity,
                **model,
                "passagers_7_jours": model.get("passagers_7_jours"),
                "passagers_30_jours": model.get("passagers_30_jours"),
                "remplissage_7_jours": None,
            }
            total = sum(r["passagers"] for r in rows)
            popular.append(
                {
                    **identity,
                    "passagers": total,
                    "departs": len(rows),
                    "remplissage_observe": round(
                        total / max(1, sum(r["capacite"] for r in rows)) * 100, 1
                    ),
                }
            )
            daily = defaultdict(int)
            slots = defaultdict(list)
            for r in rows:
                daily[r["date"]] += r["passagers"]
                slots[r["heure"]].append(r)
            values = list(daily.values())
            deviation = pstdev(values) if len(values) >= 14 else 0
            for day, value in daily.items():
                if deviation and abs(value - mean(values)) > 2 * deviation:
                    anomalies.append(
                        {
                            **identity,
                            "date": day,
                            "valeur": value,
                            "moyenne": round(mean(values), 1),
                            "type": "VOLUME_RESERVATIONS",
                            "unite": "places",
                            "raison": "Volume de places confirmées inhabituel (> 2 écarts types). Vérifier le contexte et les événements locaux.",
                        }
                    )
            if model["qualite"] == "EXPLOITABLE":
                capacity = mean([r["capacite"] for r in rows])
                suggestions = planning_suggestions(
                    model["jours"], planned[key], capacity
                )
                ranked_slots = sorted(
                    [
                        {
                            "heure": h,
                            "departs_observes": len(rs),
                            "remplissage": round(
                                sum(r["passagers"] for r in rs)
                                / sum(r["capacite"] for r in rs)
                                * 100,
                                1,
                            ),
                        }
                        for h, rs in slots.items()
                        if len(rs) >= 4
                    ],
                    key=lambda r: (
                        -r["remplissage"],
                        -r["departs_observes"],
                        r["heure"],
                    ),
                )[:3]
                offered = sum(d["places_planifiees"] for d in suggestions)
                result["remplissage_7_jours"] = (
                    round(model["passagers_7_jours"] / offered * 100, 1)
                    if offered
                    else None
                )
                recommendations.append(
                    {
                        **identity,
                        "jours": suggestions,
                        "horaires": ranked_slots,
                        "departs_recommandes": sum(
                            d["departs_supplementaires"] for d in suggestions
                        ),
                        "raison": "Départs supplémentaires à étudier sur les 7 prochains jours, à 80 % de remplissage cible. Horaires classés selon le remplissage observé (4 départs minimum). Vérifier véhicules, chauffeurs et quais dans le planning.",
                    }
                )
            forecasts.append(result)
        # Daily receipts use actual validation dates in the station timezone, not departure dates.
        receipts = defaultdict(lambda: defaultdict(float))
        query = (
            select(
                Paiement, Depart.id_itineraire, Depart.id_cooperative, Depart.id_gare
            )
            .join(Reservation, Paiement.id_reservation == Reservation.id)
            .join(Depart, Reservation.id_depart == Depart.id)
        )
        query = query.where(
            Paiement.statut == PaiementStatus.VALIDE,
            Paiement.date_validation.is_not(None),
            func.date(
                func.timezone(str(local_timezone()), Paiement.date_validation)
            ).between(start, reference - timedelta(days=1)),
        )
        for payment, route, coop, station in self.db.execute(
            self._scope(query, cooperative_ids)
        ):
            receipts[(route, coop, station)][
                local_date(payment.date_validation)
            ] += float(payment.montant)
        for key, amounts in receipts.items():
            values = list(amounts.values())
            if len(values) < 14:
                continue
            avg, deviation = mean(values), pstdev(values)
            for day, value in amounts.items():
                if deviation and abs(value - avg) > 2 * deviation:
                    anomalies.append(
                        {
                            "id_itineraire": key[0],
                            "id_cooperative": key[1],
                            "id_gare": key[2],
                            "libelle": labels.get(key[0], f"Itinéraire #{key[0]}"),
                            "date": day,
                            "valeur": round(value, 2),
                            "moyenne": round(avg, 2),
                            "type": "RECETTES_INHABITUELLES",
                            "unite": "Ar",
                            "raison": "Encaissements validés bruts inhabituels (> 2 écarts types, au moins 14 jours avec encaissements). Examiner les paiements et remboursements ; ce signal ne démontre pas une erreur.",
                        }
                    )
        return {
            "date_reference": reference,
            "periode_observee": {"du": start, "au": reference - timedelta(days=1)},
            "previsions": forecasts,
            "recommandations": recommendations,
            "destinations_demandees": sorted(popular, key=lambda r: -r["passagers"]),
            "anomalies": sorted(anomalies, key=lambda r: r["date"], reverse=True),
            "resume": {
                "itineraires_exploitables": sum(
                    item["qualite"] == "EXPLOITABLE" for item in forecasts
                ),
                "departs_a_etudier": sum(
                    item["departs_recommandes"] for item in recommendations
                ),
                "itineraires_sous_tension": len(
                    [item for item in recommendations if item["departs_recommandes"]]
                ),
                "points_a_verifier": len(anomalies),
            },
            "priorites": priorities,
            "limites": "Estimation de l’activité confirmée, pas de la demande non satisfaite. Les jours sans service comptent zéro activité. Historique de 90 jours, moyenne pondérée sur 30 jours calendaires (65 %) et saisonnalité hebdomadaire (35 %). Pas de prise en compte automatique des fêtes, vacances ou événements. Aucun départ n’est créé ou supprimé automatiquement. Les indicateurs historiques utilisent l’état actuel des réservations, sans reconstitution de leur état passé.",
        }
