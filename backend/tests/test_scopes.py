"""What each role may see: station agents, staff precedence over the passenger role."""

import uuid

from sqlalchemy import select

from app.models import Cooperative, Depart, Gare, GareAgent, GareCooperative, Role, User
from app.models.user import UserRole
from app.services.authentication.password import hash_password
from tests.helpers import API

PASSWORD = "Agent123!"


def create_user(db, *roles: str) -> User:
    user = User(name="Test", first_name="Scope", email=f"scope-{uuid.uuid4().hex[:10]}@cooperative.com", password_hash=hash_password(PASSWORD), is_active=True)
    for role in roles:
        user.roles.append(db.scalar(select(Role).where(Role.libelle == role)))
    db.add(user)
    db.commit()
    return user


def headers_for(client, user: User) -> dict[str, str]:
    token = client.post(f"{API}/auth/login", json={"email": user.email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def cooperatives_at(db, gare_id: int) -> set[int]:
    return set(db.scalars(select(GareCooperative.id_cooperative).where(GareCooperative.id_gare == gare_id, GareCooperative.is_active.is_(True))))


def test_agent_attached_to_a_station_sees_its_departures(client, db, admin_headers):
    """I-B07: an agent with no cooperative membership used to see nothing."""
    gare = db.scalar(select(Gare).where(Gare.ville == "Toamasina"))
    agent = create_user(db, UserRole.AGENT_GARE)
    headers = headers_for(client, agent)
    assert client.get(f"{API}/departs", headers=headers).json()["total"] == 0

    response = client.post(f"{API}/gares/{gare.id}/agents/{agent.id}", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()] == [agent.id] or agent.id in [item["id"] for item in response.json()]

    departs = client.get(f"{API}/departs?page_size=100", headers=headers).json()
    assert departs["total"] > 0
    allowed = cooperatives_at(db, gare.id)
    assert {item["id_cooperative"] for item in departs["items"]} <= allowed


def test_agent_can_only_be_attached_to_one_station(client, db, admin_headers):
    agent = create_user(db, UserRole.AGENT_GARE)
    first, second = db.scalars(select(Gare.id).order_by(Gare.id).limit(2)).all()
    assert client.post(f"{API}/gares/{first}/agents/{agent.id}", headers=admin_headers).status_code == 200
    assert client.post(f"{API}/gares/{second}/agents/{agent.id}", headers=admin_headers).status_code == 409
    assert client.delete(f"{API}/gares/{first}/agents/{agent.id}", headers=admin_headers).status_code == 204
    assert client.post(f"{API}/gares/{second}/agents/{agent.id}", headers=admin_headers).status_code == 200


def test_only_agents_can_be_attached_to_a_station(client, db, admin_headers):
    passenger = create_user(db, UserRole.PASSAGER)
    gare_id = db.scalar(select(Gare.id).limit(1))
    assert client.post(f"{API}/gares/{gare_id}/agents/{passenger.id}", headers=admin_headers).status_code == 422


def test_agent_cash_desk_scope_is_their_station(client, db, login):
    headers = login("agent.toamasina@cooperative.com")
    gare_id = db.scalar(select(Gare.id).where(Gare.ville == "Toamasina"))
    caisses = client.get(f"{API}/caisses?page_size=100", headers=headers).json()["items"]
    assert caisses and {item["id_gare"] for item in caisses} == {gare_id}


def test_staff_role_takes_precedence_over_passenger_role(client, db):
    """I-B08: a cooperative manager who also has the passenger role saw only their own bookings."""
    cooperative = db.scalar(select(Cooperative).where(Cooperative.sigle == "FTE"))
    manager = create_user(db, UserRole.PASSAGER, UserRole.RESPONSABLE_COOPERATIVE)
    cooperative.responsable_id = manager.id
    db.commit()
    headers = headers_for(client, manager)
    reservations = client.get(f"{API}/reservations?page_size=50", headers=headers).json()
    assert reservations["total"] > 0
    departs = client.get(f"{API}/departs?page_size=100", headers=headers).json()["items"]
    assert departs and {item["id_cooperative"] for item in departs} == {cooperative.id}


def test_cooperative_manager_sees_only_own_departures(client, db, login):
    headers = login("responsable.fte@cooperative.com")
    fte = db.scalar(select(Cooperative.id).where(Cooperative.sigle == "FTE"))
    departs = client.get(f"{API}/departs?page_size=100", headers=headers).json()["items"]
    assert departs and {item["id_cooperative"] for item in departs} == {fte}
    other = db.scalar(select(Depart.id).where(Depart.id_cooperative != fte).limit(1))
    assert client.get(f"{API}/departs/{other}", headers=headers).status_code in (403, 404)


def test_passenger_browses_every_departure(client, login, db):
    headers = login("passager01@cooperative.com")
    assert client.get(f"{API}/departs?page_size=1", headers=headers).json()["total"] == db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Depart))


def test_requests_without_token_are_rejected(client):
    assert client.get(f"{API}/reservations").status_code == 401
    assert client.get(f"{API}/departs").status_code == 401


def test_station_agents_listing_requires_gare_read(client, db, login):
    gare_id = db.scalar(select(Gare.id).limit(1))
    assert client.get(f"{API}/gares/{gare_id}/agents", headers=login("passager02@cooperative.com")).status_code == 403
    agents = client.get(f"{API}/gares/{gare_id}/agents", headers=login("responsable.gare1@cooperative.com"))
    assert agents.status_code == 200
    assert db.scalar(select(GareAgent).where(GareAgent.id_gare == gare_id)) is not None


def test_eligible_agents_lists_unattached_agents_only(client, db, login):
    agent = create_user(db, UserRole.AGENT_GARE)
    gare_id = db.scalar(select(Gare.id).limit(1))
    headers = login("responsable.gare1@cooperative.com")
    eligible = client.get(f"{API}/gares/{gare_id}/eligible-agents", headers=headers)
    assert eligible.status_code == 200, eligible.text
    ids = {item["id"] for item in eligible.json()}
    assert agent.id in ids
    attached = set(db.scalars(select(GareAgent.id_user)))
    assert not ids & attached
