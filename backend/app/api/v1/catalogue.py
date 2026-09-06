from __future__ import annotations

from flask import g, jsonify, request

from app.api.v1 import api_v1
from app.core.parsing import parse_uuid
from app.schemas.catalogue import (
    ArchetypeRead,
    GenericSolutionRead,
    GenericSolutionSummary,
    SubsystemRead,
    SystemRead,
)
from app.schemas.envelope import data_response
from app.services.catalogue import CatalogService


@api_v1.get("/systems")
def list_systems():
    service = CatalogService(g.db)
    data = [
        SystemRead.model_validate(item).model_dump(mode="json") for item in service.list_systems()
    ]
    return jsonify(data_response(data))


@api_v1.get("/systems/<system_id>")
def get_system(system_id: str):
    service = CatalogService(g.db)
    item = service.get_system(parse_uuid(system_id))
    return jsonify(data_response(SystemRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/systems/by-code/<code>")
def get_system_by_code(code: str):
    service = CatalogService(g.db)
    item = service.get_system_by_code(code)
    return jsonify(data_response(SystemRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/subsystems")
def list_subsystems():
    system_id = request.args.get("system_id")
    service = CatalogService(g.db)
    data = [
        SubsystemRead.model_validate(item).model_dump(mode="json")
        for item in service.list_subsystems(
            system_id=parse_uuid(system_id) if system_id else None,
        )
    ]
    return jsonify(data_response(data))


@api_v1.get("/subsystems/<subsystem_id>")
def get_subsystem(subsystem_id: str):
    service = CatalogService(g.db)
    item = service.get_subsystem(parse_uuid(subsystem_id))
    return jsonify(data_response(SubsystemRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/subsystems/by-code/<code>")
def get_subsystem_by_code(code: str):
    service = CatalogService(g.db)
    item = service.get_subsystem_by_code(code)
    return jsonify(data_response(SubsystemRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/archetypes")
def list_archetypes():
    subsystem_id = request.args.get("subsystem_id")
    service = CatalogService(g.db)
    data = [
        ArchetypeRead.model_validate(item).model_dump(mode="json")
        for item in service.list_archetypes(
            subsystem_id=parse_uuid(subsystem_id) if subsystem_id else None,
        )
    ]
    return jsonify(data_response(data))


@api_v1.get("/archetypes/<archetype_id>")
def get_archetype(archetype_id: str):
    service = CatalogService(g.db)
    item = service.get_archetype(parse_uuid(archetype_id))
    return jsonify(data_response(ArchetypeRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/archetypes/by-code/<code>")
def get_archetype_by_code(code: str):
    service = CatalogService(g.db)
    item = service.get_archetype_by_code(code)
    return jsonify(data_response(ArchetypeRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/generic-solutions")
def list_generic_solutions():
    archetype_id = request.args.get("archetype_id")
    service = CatalogService(g.db)
    data = [
        GenericSolutionSummary.model_validate(item).model_dump(mode="json")
        for item in service.list_generic_solutions(
            archetype_id=parse_uuid(archetype_id) if archetype_id else None,
        )
    ]
    return jsonify(data_response(data))


@api_v1.get("/generic-solutions/<solution_id>")
def get_generic_solution(solution_id: str):
    service = CatalogService(g.db)
    item = service.get_generic_solution(parse_uuid(solution_id))
    return jsonify(data_response(GenericSolutionRead.model_validate(item).model_dump(mode="json")))


@api_v1.get("/generic-solutions/by-code/<code>")
def get_generic_solution_by_code(code: str):
    service = CatalogService(g.db)
    item = service.get_generic_solution_by_code(code)
    return jsonify(data_response(GenericSolutionRead.model_validate(item).model_dump(mode="json")))
