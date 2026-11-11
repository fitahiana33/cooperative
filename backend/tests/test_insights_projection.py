from datetime import date, timedelta

from types import SimpleNamespace

from app.services.insights import (
    project_passengers,
    forecast_history,
    planning_suggestions,
)


def test_constant_daily_demand_is_projected_over_whole_horizon():
    assert project_passengers(date(2026, 11, 9), 10, {}, 7) == 70
    assert project_passengers(date(2026, 11, 9), 10, {}, 30) == 300


def test_weekly_projection_uses_all_seven_weekdays():
    weekdays = {day: day * 10 for day in range(1, 8)}
    expected = 7 * 10 * 0.65 + sum(weekdays.values()) * 0.35
    assert project_passengers(date(2026, 11, 9), 10, weekdays, 7) == expected


def test_no_observed_demand_does_not_create_artificial_passengers():
    assert project_passengers(date(2026, 11, 9), 0, {}, 30) == 0


def test_sparse_and_stale_history_must_not_produce_departure_forecasts():
    reference = date(2026, 11, 9)
    for dates in [[1], list(range(40, 70)), list(range(1, 12))]:
        result = forecast_history(
            reference,
            [{"date": reference - timedelta(days=d), "passagers": 20} for d in dates],
        )
        assert result["qualite"] == "INSUFFISANT"
        assert "jours" not in result


def test_daily_forecasts_cover_the_same_horizon_as_the_total():
    reference = date(2026, 11, 9)
    result = forecast_history(
        reference,
        [
            {"date": reference - timedelta(days=d), "passagers": 10}
            for d in range(1, 61)
        ],
    )
    assert result["qualite"] == "EXPLOITABLE"
    assert result["passagers_7_jours"] == 70
    assert result["passagers_30_jours"] == 300
    assert [d["date"] for d in result["jours"]] == [
        reference + timedelta(days=d) for d in range(1, 8)
    ]


def test_zero_activity_remains_zero_even_with_sufficient_history():
    reference = date(2026, 11, 9)
    result = forecast_history(
        reference,
        [{"date": reference - timedelta(days=d), "passagers": 0} for d in range(1, 31)],
    )
    assert result["passagers_30_jours"] == 0


def test_planned_capacity_avoids_recommending_departures_already_provided():
    tomorrow = date(2026, 11, 12)
    planned = [
        SimpleNamespace(
            date_depart=tomorrow,
            nombre_places=50,
            places_bloquees=0,
            places_reservees=10,
        )
    ]
    result = planning_suggestions([{"date": tomorrow, "passagers": 40}], planned, 20)[0]
    assert result["departs_supplementaires"] == 0
    assert result["places_planifiees"] == 50


def test_blocked_seats_and_existing_bookings_are_considered_on_the_correct_day():
    tomorrow = date(2026, 11, 12)
    planned = [
        SimpleNamespace(
            date_depart=tomorrow,
            nombre_places=20,
            places_bloquees=10,
            places_reservees=10,
        )
    ]
    days = [
        {"date": tomorrow, "passagers": 2},
        {"date": tomorrow + timedelta(days=1), "passagers": 20},
    ]
    result = planning_suggestions(days, planned, 20)
    assert result[0]["places_planifiees"] == 10
    assert (
        result[0]["departs_supplementaires"] == 1
    )  # Existing bookings exceed the 80% target.
    assert result[1]["departs_planifies"] == 0
    assert (
        result[1]["departs_supplementaires"] == 2
    )  # 20 passengers need two 20-seat vehicles at 80%.
