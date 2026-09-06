from __future__ import annotations

from http import HTTPStatus

from flask import current_app, g, jsonify, request

from app.api.v1 import api_v1
from app.api.v1.dependencies import require_role
from app.core.parsing import parse_uuid
from app.core.permissions import UserRole
from app.schemas.commercial import (
    CommercialSolutionCreate,
    CommercialSolutionRead,
    CommercialSolutionUpdate,
)
from app.schemas.envelope import data_response
from app.services.commercial import CommercialSolutionService


@api_v1.get("/manufacturer/commercial-solutions")
@require_role(UserRole.MANUFACTURER)
def list_manufacturer_solutions():
    service = CommercialSolutionService(g.db)
    data = [
        CommercialSolutionRead.model_validate(item).model_dump(mode="json")
        for item in service.list_own(g.current_user)
    ]
    return jsonify(data_response(data))


@api_v1.post("/manufacturer/commercial-solutions")
@require_role(UserRole.MANUFACTURER)
def create_manufacturer_solution():
    dto = CommercialSolutionCreate.model_validate(request.get_json(silent=True) or {})
    item = CommercialSolutionService(g.db).create(g.current_user, dto)
    return jsonify(data_response(CommercialSolutionRead.model_validate(item).model_dump(mode="json"))), HTTPStatus.CREATED


@api_v1.get("/manufacturer/commercial-solutions/<solution_id>")
@require_role(UserRole.MANUFACTURER)
def get_manufacturer_solution(solution_id: str):
    item = CommercialSolutionService(g.db).get_own(g.current_user, parse_uuid(solution_id))
    return jsonify(data_response(CommercialSolutionRead.model_validate(item).model_dump(mode="json")))


@api_v1.patch("/manufacturer/commercial-solutions/<solution_id>")
@require_role(UserRole.MANUFACTURER)
def update_manufacturer_solution(solution_id: str):
    dto = CommercialSolutionUpdate.model_validate(request.get_json(silent=True) or {})
    item = CommercialSolutionService(g.db).update_own(g.current_user, parse_uuid(solution_id), dto)
    return jsonify(data_response(CommercialSolutionRead.model_validate(item).model_dump(mode="json")))


@api_v1.delete("/manufacturer/commercial-solutions/<solution_id>")
@require_role(UserRole.MANUFACTURER)
def delete_manufacturer_solution(solution_id: str):
    paths = CommercialSolutionService(g.db).delete_own(g.current_user, parse_uuid(solution_id))
    storage = current_app.extensions["file_storage"]
    for relative_path in paths:
        storage.delete(relative_path)
    return "", HTTPStatus.NO_CONTENT


@api_v1.post("/manufacturer/commercial-solutions/<solution_id>/submit")
@require_role(UserRole.MANUFACTURER)
def submit_manufacturer_solution(solution_id: str):
    item = CommercialSolutionService(g.db).submit(g.current_user, parse_uuid(solution_id))
    return jsonify(data_response(CommercialSolutionRead.model_validate(item).model_dump(mode="json")))
