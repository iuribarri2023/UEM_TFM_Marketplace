from __future__ import annotations

from flask import g, jsonify, request

from app.api.v1 import api_v1
from app.api.v1.dependencies import require_role
from app.core.parsing import parse_uuid
from app.core.permissions import UserRole
from app.schemas.commercial import CommercialSolutionRead, RejectRequest
from app.schemas.envelope import data_response
from app.services.commercial import CommercialSolutionService


@api_v1.get("/admin/commercial-solutions/submitted")
@require_role(UserRole.ADMIN)
def list_submitted_solutions():
    data = [
        CommercialSolutionRead.model_validate(item).model_dump(mode="json")
        for item in CommercialSolutionService(g.db).list_submitted_for_admin(g.current_user)
    ]
    return jsonify(data_response(data))


@api_v1.post("/admin/commercial-solutions/<solution_id>/approve")
@require_role(UserRole.ADMIN)
def approve_solution(solution_id: str):
    item = CommercialSolutionService(g.db).approve(g.current_user, parse_uuid(solution_id))
    return jsonify(data_response(CommercialSolutionRead.model_validate(item).model_dump(mode="json")))


@api_v1.post("/admin/commercial-solutions/<solution_id>/reject")
@require_role(UserRole.ADMIN)
def reject_solution(solution_id: str):
    dto = RejectRequest.model_validate(request.get_json(silent=True) or {})
    item = CommercialSolutionService(g.db).reject(
        g.current_user, parse_uuid(solution_id), reason=dto.reason
    )
    return jsonify(data_response(CommercialSolutionRead.model_validate(item).model_dump(mode="json")))
