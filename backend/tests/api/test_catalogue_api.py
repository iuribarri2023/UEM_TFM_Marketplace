import pytest

pytestmark = pytest.mark.postgres


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_openapi_and_swagger_docs(client):
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert b"SwaggerUIBundle" in docs.data

    openapi = client.get("/openapi.yaml")
    assert openapi.status_code == 200
    assert openapi.text.startswith("openapi: 3.1.0")
    assert "/api/v1/generic-solutions/by-code/{code}" in openapi.text


def test_catalogue_serialization_and_filters(client, catalogue):
    systems = client.get("/api/v1/systems")
    assert systems.status_code == 200
    system_id = systems.get_json()["data"][0]["id"]

    subsystems = client.get(f"/api/v1/subsystems?system_id={system_id}")
    assert subsystems.status_code == 200
    assert {item["code"] for item in subsystems.get_json()["data"]} == {"FAC", "ROF", "WIN"}

    archetype_id = str(catalogue["facade"].archetype_id)
    solutions = client.get(f"/api/v1/generic-solutions?archetype_id={archetype_id}")
    assert solutions.status_code == 200
    assert [item["code"] for item in solutions.get_json()["data"]] == ["FAC-VEN-001"]

    detail = client.get(f"/api/v1/generic-solutions/{catalogue['facade'].id}")
    body = detail.get_json()["data"]
    assert body["code"] == "FAC-VEN-001"
    assert [slot["sequence"] for slot in body["slots"]] == [10, 20, 30]
    assert [slot["key"] for slot in body["slots"]].count("AT") == 2


def test_catalogue_lookup_by_code(client, catalogue):
    system = client.get("/api/v1/systems/by-code/ENV")
    assert system.status_code == 200
    assert system.get_json()["data"]["id"] == str(catalogue["system"].id)

    subsystem = client.get("/api/v1/subsystems/by-code/FAC")
    assert subsystem.status_code == 200
    assert subsystem.get_json()["data"]["code"] == "FAC"

    archetype = client.get("/api/v1/archetypes/by-code/FAC-VEN")
    assert archetype.status_code == 200
    assert archetype.get_json()["data"]["code"] == "FAC-VEN"

    solution = client.get("/api/v1/generic-solutions/by-code/FAC-VEN-001")
    body = solution.get_json()["data"]
    assert solution.status_code == 200
    assert body["id"] == str(catalogue["facade"].id)
    assert [slot["sequence"] for slot in body["slots"]] == [10, 20, 30]
