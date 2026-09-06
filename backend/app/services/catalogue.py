from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFound
from app.repositories.catalogue import (
    ArchetypeRepository,
    GenericSolutionRepository,
    GenericSolutionSlotRepository,
    SubsystemRepository,
    SystemRepository,
)


class CatalogService:
    def __init__(self, session: Session):
        self.systems = SystemRepository(session)
        self.subsystems = SubsystemRepository(session)
        self.archetypes = ArchetypeRepository(session)
        self.generic_solutions = GenericSolutionRepository(session)
        self.slots = GenericSolutionSlotRepository(session)

    def list_systems(self):
        return self.systems.list()

    def get_system(self, system_id: UUID):
        system = self.systems.get(system_id)
        if not system:
            raise EntityNotFound("System not found.")
        return system

    def get_system_by_code(self, code: str):
        system = self.systems.get_by_code(code)
        if not system:
            raise EntityNotFound("System not found.")
        return system

    def list_subsystems(self, *, system_id: UUID | None = None):
        return self.subsystems.list(system_id=system_id)

    def get_subsystem(self, subsystem_id: UUID):
        subsystem = self.subsystems.get(subsystem_id)
        if not subsystem:
            raise EntityNotFound("Subsystem not found.")
        return subsystem

    def get_subsystem_by_code(self, code: str):
        subsystem = self.subsystems.get_by_code(code)
        if not subsystem:
            raise EntityNotFound("Subsystem not found.")
        return subsystem

    def list_archetypes(self, *, subsystem_id: UUID | None = None):
        return self.archetypes.list(subsystem_id=subsystem_id)

    def get_archetype(self, archetype_id: UUID):
        archetype = self.archetypes.get(archetype_id)
        if not archetype:
            raise EntityNotFound("Archetype not found.")
        return archetype

    def get_archetype_by_code(self, code: str):
        archetype = self.archetypes.get_by_code(code)
        if not archetype:
            raise EntityNotFound("Archetype not found.")
        return archetype

    def list_generic_solutions(self, *, archetype_id: UUID | None = None):
        return self.generic_solutions.list(archetype_id=archetype_id)

    def get_generic_solution(self, solution_id: UUID):
        solution = self.generic_solutions.get(solution_id, include_slots=True, include_assets=True)
        if not solution:
            raise EntityNotFound("Generic solution not found.")
        solution.slots = self.slots.list_for_solution(solution.id)
        return solution

    def get_generic_solution_by_code(self, code: str):
        solution = self.generic_solutions.get_by_code(code, include_slots=True, include_assets=True)
        if not solution:
            raise EntityNotFound("Generic solution not found.")
        solution.slots = self.slots.list_for_solution(solution.id)
        return solution
