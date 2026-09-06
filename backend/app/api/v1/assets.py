from __future__ import annotations

from http import HTTPStatus

from flask import current_app, g, jsonify, request, send_file

from app.api.v1 import api_v1
from app.api.v1.dependencies import current_user, require_role
from app.core.exceptions import ValidationFailed
from app.core.parsing import parse_uuid
from app.core.permissions import UserRole
from app.schemas.assets import AssetRead
from app.schemas.envelope import data_response
from app.services.assets import AssetService


def _asset_service() -> AssetService:
    return AssetService(
        g.db,
        current_app.extensions["file_storage"],
        current_app.extensions["bim_adapter"],
    )


@api_v1.post("/manufacturer/commercial-solutions/<solution_id>/assets")
@require_role(UserRole.MANUFACTURER)
def upload_asset(solution_id: str):
    upload = request.files.get("file")
    if upload is None:
        raise ValidationFailed("File is required.")
    asset = _asset_service().upload_for_commercial_solution(
        user=g.current_user,
        solution_id=parse_uuid(solution_id),
        upload=upload,
        role=request.form.get("role", "primary_commercial_model"),
        asset_type=request.form.get("asset_type", "bim_model"),
        code=request.form.get("code") or None,
    )
    return jsonify(data_response(AssetRead.model_validate(asset).model_dump(mode="json"))), HTTPStatus.CREATED


@api_v1.get("/manufacturer/commercial-solutions/<solution_id>/assets")
@require_role(UserRole.MANUFACTURER)
def list_solution_assets(solution_id: str):
    assets = _asset_service().list_for_commercial_solution(g.current_user, parse_uuid(solution_id))
    return jsonify(data_response([AssetRead.model_validate(asset).model_dump(mode="json") for asset in assets]))


@api_v1.delete("/manufacturer/commercial-solutions/<solution_id>/assets/<asset_id>")
@require_role(UserRole.MANUFACTURER)
def delete_solution_asset(solution_id: str, asset_id: str):
    _asset_service().delete_from_commercial_solution(
        user=g.current_user,
        solution_id=parse_uuid(solution_id),
        asset_id=parse_uuid(asset_id),
    )
    return "", HTTPStatus.NO_CONTENT


@api_v1.get("/assets/<asset_id>/download")
def download_asset(asset_id: str):
    user = current_user(required=False)
    asset = _asset_service().get_downloadable_asset(user, parse_uuid(asset_id))
    storage = current_app.extensions["file_storage"]
    return send_file(
        storage.open_for_read(asset.relative_path),
        mimetype=asset.mime_type,
        as_attachment=True,
        download_name=asset.original_filename,
    )
