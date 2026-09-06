from __future__ import annotations

from flask import current_app, g, jsonify, request

from app.api.v1 import api_v1
from app.api.v1.dependencies import require_auth
from app.schemas.auth import CurrentUserRead, LoginRequest, RefreshRequest, TokenResponse
from app.schemas.envelope import data_response
from app.services.auth import AuthenticationService


@api_v1.post("/auth/login")
def login():
    dto = LoginRequest.model_validate(request.get_json(silent=True) or {})
    service = AuthenticationService(g.db, current_app.config["SETTINGS"])
    tokens = service.login(email=dto.email, password=dto.password)
    return jsonify(data_response(TokenResponse(**tokens).model_dump(mode="json")))


@api_v1.post("/auth/refresh")
def refresh():
    dto = RefreshRequest.model_validate(request.get_json(silent=True) or {})
    service = AuthenticationService(g.db, current_app.config["SETTINGS"])
    tokens = service.refresh(refresh_token=dto.refresh_token)
    return jsonify(data_response(TokenResponse(**tokens).model_dump(mode="json")))


@api_v1.get("/auth/me")
@require_auth
def me():
    return jsonify(
        data_response(CurrentUserRead.model_validate(g.current_user, from_attributes=True).model_dump(mode="json"))
    )

