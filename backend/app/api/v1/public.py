from __future__ import annotations

from flask import g, jsonify, request

from app.api.v1 import api_v1
from app.core.parsing import parse_uuid
from app.schemas.commercial import CommercialSolutionRead, ManufacturerRead
from app.schemas.envelope import data_response
from app.services.public import PublicMarketplaceService


@api_v1.get("/marketplace/commercial-solutions")
def list_public_solutions():
    service = PublicMarketplaceService(g.db)
    data = [
        CommercialSolutionRead.model_validate(item).model_dump(mode="json")
        for item in service.list_approved(
            generic_solution_id=_optional_uuid("generic_solution_id"),
            archetype_id=_optional_uuid("archetype_id"),
            subsystem_id=_optional_uuid("subsystem_id"),
            system_id=_optional_uuid("system_id"),
            manufacturer_id=_optional_uuid("manufacturer_id"),
        )
    ]
    return jsonify(data_response(data))


@api_v1.get("/marketplace/commercial-solutions/<solution_id>")
def get_public_solution(solution_id: str):
    item = PublicMarketplaceService(g.db).get_approved(parse_uuid(solution_id))
    return jsonify(data_response(CommercialSolutionRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/manufacturers")
def list_manufacturers():
    data = [
        ManufacturerRead.model_validate(item).model_dump(mode="json")
        for item in PublicMarketplaceService(g.db).list_manufacturers()
    ]
    return jsonify(data_response(data))


@api_v1.get("/manufacturers/<manufacturer_id>")
def get_manufacturer(manufacturer_id: str):
    item = PublicMarketplaceService(g.db).get_manufacturer(parse_uuid(manufacturer_id))
    return jsonify(data_response(ManufacturerRead.model_validate(item).model_dump(mode="json")))


def _optional_uuid(name: str):
    value = request.args.get(name)
    return parse_uuid(value) if value else None
