from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.catalogue import (
    Archetype,
    GenericSolution,
    GenericSolutionSlot,
    Subsystem,
    System,
)


class SystemRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[System]:
        return list(self.session.scalars(select(System).order_by(System.code)))

    def get(self, system_id: UUID) -> System | None:
        return self.session.get(System, system_id)

    def get_by_code(self, code: str) -> System | None:
        return self.session.scalar(select(System).where(System.code == code))

    def add(self, system: System) -> System:
        self.session.add(system)
        return system


class SubsystemRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self, *, system_id: UUID | None = None) -> list[Subsystem]:
        stmt = select(Subsystem).order_by(Subsystem.code)
        if system_id:
            stmt = stmt.where(Subsystem.system_id == system_id)
        return list(self.session.scalars(stmt))

    def get(self, subsystem_id: UUID) -> Subsystem | None:
        return self.session.get(Subsystem, subsystem_id)

    def get_by_code(self, code: str) -> Subsystem | None:
        return self.session.scalar(select(Subsystem).where(Subsystem.code == code))

    def add(self, subsystem: Subsystem) -> Subsystem:
        self.session.add(subsystem)
        return subsystem


class ArchetypeRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self, *, subsystem_id: UUID | None = None) -> list[Archetype]:
        stmt = select(Archetype).order_by(Archetype.code)
        if subsystem_id:
            stmt = stmt.where(Archetype.subsystem_id == subsystem_id)
        return list(self.session.scalars(stmt))

    def get(self, archetype_id: UUID) -> Archetype | None:
        return self.session.get(Archetype, archetype_id)

    def get_by_code(self, code: str) -> Archetype | None:
        return self.session.scalar(select(Archetype).where(Archetype.code == code))

    def add(self, archetype: Archetype) -> Archetype:
        self.session.add(archetype)
        return archetype


class GenericSolutionRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self, *, archetype_id: UUID | None = None) -> list[GenericSolution]:
        stmt = select(GenericSolution).order_by(GenericSolution.code)
        if archetype_id:
            stmt = stmt.where(GenericSolution.archetype_id == archetype_id)
        return list(self.session.scalars(stmt))

    def list_public(
        self,
        *,
        generic_solution_id: UUID | None = None,
        archetype_id: UUID | None = None,
        subsystem_id: UUID | None = None,
        system_id: UUID | None = None,
        manufacturer_id: UUID | None = None,
    ):
        from app.db.models.commercial import CommercialSolution

        stmt = (
            select(CommercialSolution)
            .join(GenericSolution)
            .join(Archetype)
            .join(Subsystem)
            .where(CommercialSolution.status == "APPROVED")
            .options(selectinload(CommercialSolution.assets))
            .order_by(CommercialSolution.code)
        )
        if generic_solution_id:
            stmt = stmt.where(CommercialSolution.generic_solution_id == generic_solution_id)
        if archetype_id:
            stmt = stmt.where(GenericSolution.archetype_id == archetype_id)
        if subsystem_id:
            stmt = stmt.where(Archetype.subsystem_id == subsystem_id)
        if system_id:
            stmt = stmt.where(Subsystem.system_id == system_id)
        if manufacturer_id:
            stmt = stmt.where(CommercialSolution.manufacturer_id == manufacturer_id)
        return list(self.session.scalars(stmt))

    def get(
        self,
        generic_solution_id: UUID,
        *,
        include_slots: bool = False,
        include_assets: bool = False,
    ) -> GenericSolution | None:
        stmt = select(GenericSolution).where(GenericSolution.id == generic_solution_id)
        options = []
        if include_slots:
            options.append(selectinload(GenericSolution.slots))
        if include_assets:
            options.append(selectinload(GenericSolution.assets))
        if options:
            stmt = stmt.options(*options)
        return self.session.scalar(stmt)

    def get_by_code(
        self,
        code: str,
        *,
        include_slots: bool = False,
        include_assets: bool = False,
    ) -> GenericSolution | None:
        stmt = select(GenericSolution).where(GenericSolution.code == code)
        options = []
        if include_slots:
            options.append(selectinload(GenericSolution.slots))
        if include_assets:
            options.append(selectinload(GenericSolution.assets))
        if options:
            stmt = stmt.options(*options)
        return self.session.scalar(stmt)

    def add(self, solution: GenericSolution) -> GenericSolution:
        self.session.add(solution)
        return solution


class GenericSolutionSlotRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_for_solution(self, generic_solution_id: UUID) -> list[GenericSolutionSlot]:
        stmt = (
            select(GenericSolutionSlot)
            .where(GenericSolutionSlot.generic_solution_id == generic_solution_id)
            .order_by(GenericSolutionSlot.sequence, GenericSolutionSlot.id)
        )
        return list(self.session.scalars(stmt))

    def add(self, slot: GenericSolutionSlot) -> GenericSolutionSlot:
        self.session.add(slot)
        return slot

    def replace_for_solution(
        self, generic_solution_id: UUID, slots: list[GenericSolutionSlot]
    ) -> list[GenericSolutionSlot]:
        self.session.execute(
            delete(GenericSolutionSlot).where(
                GenericSolutionSlot.generic_solution_id == generic_solution_id
            )
        )
        self.session.add_all(slots)
        return slots
