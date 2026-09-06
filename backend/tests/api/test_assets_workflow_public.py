import io

import pytest

from tests.conftest import auth_header


pytestmark = pytest.mark.postgres


def _upload_ifc(client, solution_id, headers, content: bytes = None):
    content = content or (
        b"ISO-10303-21;\nHEADER;\nFILE_NAME('fixture.ifc','2026',(),(),'', '', '');\n"
        b"FILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;"
    )
    return client.post(
        f"/api/v1/manufacturer/commercial-solutions/{solution_id}/assets",
        data={
            "role": "ifc_model",
            "asset_type": "bim",
            "file": (io.BytesIO(content), "model.ifc"),
        },
        content_type="multipart/form-data",
        headers=headers,
    )


def test_missing_ifc_submission_fails(client, users):
    response = client.post(
        f"/api/v1/manufacturer/commercial-solutions/{users['draft'].id}/submit",
        headers=auth_header(client, "m1@example.com"),
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "MISSING_IFC_FILE"


def test_invalid_ifc_upload_fails(client, users):
    response = _upload_ifc(
        client,
        users["draft"].id,
        auth_header(client, "m1@example.com"),
        content=b"not an ifc file",
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_IFC_FILE"


def test_upload_submit_approve_and_public_visibility(client, users):
    m_headers = auth_header(client, "m1@example.com")
    upload = _upload_ifc(client, users["draft"].id, m_headers)
    assert upload.status_code == 201
    asset_id = upload.get_json()["data"]["id"]
    assert upload.get_json()["data"]["sha256"]

    private_download = client.get(f"/api/v1/assets/{asset_id}/download")
    assert private_download.status_code == 403

    cross_assets = client.get(
        f"/api/v1/manufacturer/commercial-solutions/{users['draft'].id}/assets",
        headers=auth_header(client, "m2@example.com"),
    )
    assert cross_assets.status_code == 403

    submit = client.post(
        f"/api/v1/manufacturer/commercial-solutions/{users['draft'].id}/submit",
        headers=m_headers,
    )
    assert submit.status_code == 200
    assert submit.get_json()["data"]["status"] == "SUBMITTED"

    draft_not_public = client.get(f"/api/v1/marketplace/commercial-solutions/{users['draft'].id}")
    assert draft_not_public.status_code == 404

    approve = client.post(
        f"/api/v1/admin/commercial-solutions/{users['draft'].id}/approve",
        headers=auth_header(client, "admin@example.com"),
    )
    assert approve.status_code == 200
    assert approve.get_json()["data"]["status"] == "APPROVED"

    public_list = client.get("/api/v1/marketplace/commercial-solutions")
    assert [item["id"] for item in public_list.get_json()["data"]] == [str(users["draft"].id)]

    download = client.get(f"/api/v1/assets/{asset_id}/download")
    assert download.status_code == 200


def test_rejected_solution_is_not_public(client, users, db_session):
    users["draft"].status = "SUBMITTED"
    db_session.commit()
    headers = auth_header(client, "admin@example.com")
    response = client.post(
        f"/api/v1/admin/commercial-solutions/{users['draft'].id}/reject",
        json={"reason": "Incomplete documentation"},
        headers=headers,
    )
    assert response.status_code == 200
    assert client.get(f"/api/v1/marketplace/commercial-solutions/{users['draft'].id}").status_code == 404


def test_invalid_transition_is_rejected(client, users):
    response = client.post(
        f"/api/v1/admin/commercial-solutions/{users['draft'].id}/approve",
        headers=auth_header(client, "admin@example.com"),
    )
    assert response.status_code == 409
