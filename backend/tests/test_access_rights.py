"""Admin protection, cooperative self-extension, minimal user lists."""

from sqlalchemy import select

from app.core.config import settings
from app.models import Cooperative, Gare, Itineraire, Permission, Role, User
from app.models.user import UserRole
from tests.helpers import API
from tests.test_scopes import create_user, headers_for


def delegate(db, user: User, *codes: str) -> None:
    """Give a user a custom role holding the given permissions."""
    role = Role(libelle=f"delegue-{user.id}", description="test", is_active=True)
    role.permissions.extend(db.scalars(select(Permission).where(Permission.code.in_(codes))))
    db.add(role)
    user.roles.append(role)
    db.commit()


def test_delegated_user_manager_cannot_touch_admin_accounts(client, db):
    """I-S07."""
    manager = create_user(db, UserRole.RESPONSABLE_GARE)
    delegate(db, manager, "USER_UPDATE", "USER_CREATE", "ROLE_MANAGE")
    headers = headers_for(client, manager)
    admin = db.scalar(select(User).where(User.email == settings.default_admin_email))
    admin_role = db.scalar(select(Role).where(Role.libelle == UserRole.ADMIN))

    assert client.put(f"{API}/users/{admin.id}", headers=headers, json={"password": "Hacked123"}).status_code == 403
    assert client.post(f"{API}/users", headers=headers, json={"name": "X", "first_name": "Y", "email": "x.y@cooperative.com", "role": "admin", "password": "Secret123"}).status_code == 403
    assert client.post(f"{API}/users/{manager.id}/roles/{admin_role.id}", headers=headers).status_code == 403
    assert client.post(f"{API}/roles/{admin_role.id}/users/{manager.id}", headers=headers).status_code == 403
    # Non-admin accounts remain manageable.
    passenger = create_user(db, UserRole.PASSAGER)
    assert client.put(f"{API}/users/{passenger.id}", headers=headers, json={"telephone": "+261 34 11 111 11"}).status_code == 200


def test_admin_can_be_demoted_unless_last_one(client, db, admin_headers):
    """I-B20."""
    second_admin = create_user(db, UserRole.ADMIN)
    admin_role = db.scalar(select(Role).where(Role.libelle == UserRole.ADMIN))
    assert client.delete(f"{API}/users/{second_admin.id}/roles/{admin_role.id}", headers=admin_headers).status_code == 200
    admin = db.scalar(select(User).where(User.email == settings.default_admin_email))
    assert client.delete(f"{API}/users/{admin.id}/roles/{admin_role.id}", headers=admin_headers).status_code == 409


def test_cooperative_manager_cannot_attach_own_cooperative_anywhere(client, db, login):
    """I-S05."""
    headers = login("responsable.fte@cooperative.com")
    fte = db.scalar(select(Cooperative).where(Cooperative.sigle == "FTE"))
    toliara = db.scalar(select(Gare.id).where(Gare.ville == "Toliara"))
    assert client.post(f"{API}/cooperatives/{fte.id}/attach-gare/{toliara}", headers=headers).status_code == 403
    itinerary = db.scalar(select(Itineraire.id).order_by(Itineraire.id.desc()).limit(1))
    assert client.post(f"{API}/itineraires/{itinerary}/cooperatives/{fte.id}", headers=headers).status_code == 403


def test_member_candidates_expose_no_contact_details(client, db, login):
    headers = login("responsable.fte@cooperative.com")
    fte = db.scalar(select(Cooperative.id).where(Cooperative.sigle == "FTE"))
    response = client.get(f"{API}/cooperatives/{fte}/eligible-members", headers=headers)
    assert response.status_code == 200
    assert response.json() and set(response.json()[0]) == {"id", "name", "first_name", "email"}
