from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFound
from app.repositories.catalogue import GenericSolutionRepository
from app.repositories.commercial import CommercialSolutionRepository, ManufacturerRepository


class PublicMarketplaceService:
    def __init__(self, session: Session):
        self.generic_solutions = GenericSolutionRepository(session)
        self.commercial_solutions = CommercialSolutionRepository(session)
        self.manufacturers = ManufacturerRepository(session)

    def list_approved(
        self,
        *,
        generic_solution_id: UUID | None = None,
        archetype_id: UUID | None = None,
        subsystem_id: UUID | None = None,
        system_id: UUID | None = None,
        manufacturer_id: UUID | None = None,
    ):
        return self.generic_solutions.list_public(
            generic_solution_id=generic_solution_id,
            archetype_id=archetype_id,
            subsystem_id=subsystem_id,
            system_id=system_id,
            manufacturer_id=manufacturer_id,
        )

    def get_approved(self, solution_id: UUID):
        solution = self.commercial_solutions.get(solution_id, include_assets=True)
        if not solution or solution.status != "APPROVED":
            raise EntityNotFound("Approved commercial solution not found.")
        return solution

    def list_manufacturers(self):
        return [item for item in self.manufacturers.list() if item.status == "ACTIVE"]

    def get_manufacturer(self, manufacturer_id: UUID):
        manufacturer = self.manufacturers.get(manufacturer_id)
        if not manufacturer or manufacturer.status != "ACTIVE":
            raise EntityNotFound("Manufacturer not found.")
        return manufacturer
