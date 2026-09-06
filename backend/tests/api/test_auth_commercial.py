import pytest

from tests.conftest import auth_header


pytestmark = pytest.mark.postgres


def test_login_refresh_and_me(client, users):
    response = client.post("/api/v1/auth/login", json={"email": "m1@example.com", "password": "secret"})
    assert response.status_code == 200
    refresh_token = response.get_json()["data"]["refresh_token"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200

    me = client.get("/api/v1/auth/me", headers=auth_header(client, "m1@example.com"))
    assert me.status_code == 200
    assert me.get_json()["data"]["role"] == "MANUFACTURER"


def test_manufacturer_create_uses_authenticated_ownership(client, users, catalogue):
    response = client.post(
        "/api/v1/manufacturer/commercial-solutions",
        json={
            "generic_solution_id": str(catalogue["facade"].id),
            "code": "COM-NEW",
            "name_es": "Nuevo producto",
            "manufacturer_id": str(users["m2"].id),
        },
        headers=auth_header(client, "m1@example.com"),
    )
    assert response.status_code == 201
    body = response.get_json()["data"]
    assert body["manufacturer_id"] == str(users["m1"].id)


def test_cross_manufacturer_access_is_forbidden(client, users):
    response = client.get(
        f"/api/v1/manufacturer/commercial-solutions/{users['draft'].id}",
        headers=auth_header(client, "m2@example.com"),
    )
    assert response.status_code == 403


def test_admin_cannot_use_manufacturer_endpoint(client, users):
    response = client.get(
        "/api/v1/manufacturer/commercial-solutions",
        headers=auth_header(client, "admin@example.com"),
    )
    assert response.status_code == 403

