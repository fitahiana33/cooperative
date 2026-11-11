"""Self-service accounts and private avatars without administration privileges."""
import io

import pytest
from PIL import Image

from app.models.user import UserRole
from app.services.user.profile import MAX_PHOTO_BYTES, photo_path
from tests.helpers import API
from tests.test_scopes import create_user, headers_for


@pytest.fixture
def personal_account(client, db):
    user = create_user(db, UserRole.PASSAGER)
    return user, headers_for(client, user)


def image_bytes():
    output = io.BytesIO()
    image = Image.new("RGB", (1200, 600), "green")
    exif = Image.Exif()
    exif[270] = "Private camera metadata"
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def upload(client, headers, content):
    return client.put(f"{API}/users/me/photo", headers=headers, files={"file": ("../../picture.jpg", content, "image/jpeg")})


def test_profile_is_available_without_user_read(client, personal_account):
    user, headers = personal_account
    assert client.get(f"{API}/users/{user.id}", headers=headers).status_code == 403
    response = client.put(f"{API}/users/me", headers=headers, json={"name": "  Profil  ", "first_name": " Personnel ", "telephone": "  ", "address": None})
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Profil"
    assert response.json()["telephone"] is None
    assert client.get(f"{API}/auth/me", headers=headers).json()["name"] == "Profil"


@pytest.mark.parametrize("payload", [{"name": None}, {"name": "   "}, {"first_name": " "}, {"role": "admin"}, {"photo_version": "a" * 32}])
def test_self_service_rejects_invalid_or_privileged_fields(client, personal_account, payload):
    _, headers = personal_account
    assert client.put(f"{API}/users/me", headers=headers, json=payload).status_code == 422


def test_private_photo_lifecycle_and_sanitization(client, db, personal_account, admin_headers):
    user, headers = personal_account
    assert client.get(f"{API}/users/me/photo", headers=headers).status_code == 404
    response = upload(client, headers, image_bytes())
    assert response.status_code == 200, response.text
    version = response.json()["photo_version"]
    path = photo_path(version)
    assert path.is_file()
    assert client.get(f"{API}/auth/me", headers=headers).json()["photo_version"] == version
    downloaded = client.get(f"{API}/users/me/photo", headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.headers["cache-control"] == "private, no-store"
    with Image.open(io.BytesIO(downloaded.content)) as photo:
        assert photo.format == "JPEG"
        assert photo.size == (512, 256)
        assert not photo.getexif()
    stranger = headers_for(client, create_user(db, UserRole.PASSAGER))
    assert client.get(f"{API}/users/{user.id}/photo", headers=stranger).status_code == 403
    assert client.get(f"{API}/users/{user.id}/photo").status_code == 401
    assert client.get(f"{API}/users/{user.id}/photo", headers=admin_headers).status_code == 200
    assert client.put(f"{API}/users/{user.id}/photo", headers=stranger, files={"file": ("x.jpg", image_bytes())}).status_code == 405
    replacement = upload(client, headers, image_bytes()).json()["photo_version"]
    assert replacement != version
    assert not path.exists()
    assert client.delete(f"{API}/users/me/photo", headers=headers).json()["photo_version"] is None
    assert not photo_path(replacement).exists()
    assert client.get(f"{API}/users/me/photo", headers=headers).status_code == 404
    assert client.delete(f"{API}/users/me/photo", headers=headers).status_code == 200


def test_invalid_photo_keeps_previous_photo(client, personal_account):
    _, headers = personal_account
    previous = upload(client, headers, image_bytes()).json()["photo_version"]
    for content, expected in [(b'<svg onload="alert(1)"/>', 400), (b"x" * (MAX_PHOTO_BYTES + 1), 413), (b"", 400)]:
        assert upload(client, headers, content).status_code == expected
        assert client.get(f"{API}/users/me", headers=headers).json()["photo_version"] == previous
        assert photo_path(previous).is_file()
    client.delete(f"{API}/users/me/photo", headers=headers)


def test_deleted_account_removes_photo_file(client, db, personal_account, admin_headers):
    user, headers = personal_account
    version = upload(client, headers, image_bytes()).json()["photo_version"]
    assert client.delete(f"{API}/users/{user.id}", headers=admin_headers).status_code == 204
    assert not photo_path(version).exists()


@pytest.mark.parametrize("format", ["PNG", "WEBP"])
def test_transparent_images_are_reencoded_on_a_white_background(client, personal_account, format):
    _, headers = personal_account
    content = io.BytesIO()
    Image.new("RGBA", (32, 32), (255, 0, 0, 0)).save(content, format=format)
    response = upload(client, headers, content.getvalue())
    assert response.status_code == 200, response.text
    downloaded = client.get(f"{API}/users/me/photo", headers=headers)
    with Image.open(io.BytesIO(downloaded.content)) as photo:
        assert photo.getpixel((0, 0)) == (255, 255, 255)
        assert photo.format == "JPEG"
    client.delete(f"{API}/users/me/photo", headers=headers)


def test_excessive_pixel_dimensions_are_refused(client, personal_account):
    _, headers = personal_account
    content = io.BytesIO()
    Image.new("RGB", (4000, 2501), "white").save(content, format="PNG")
    assert upload(client, headers, content.getvalue()).status_code == 400
    assert client.get(f"{API}/users/me", headers=headers).json()["photo_version"] is None
