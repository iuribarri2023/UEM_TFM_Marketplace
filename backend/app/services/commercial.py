from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    EntityNotFound,
    InvalidWorkflowTransition,
    MissingIfcFile,
    PermissionDenied,
)
from app.core.permissions import UserRole, is_admin
from app.db.models.commercial import CommercialSolution, User
from app.db.transaction import transactional
from app.domain.commercial import CommercialSolutionStatus
from app.repositories.catalogue import GenericSolutionRepository
from app.repositories.commercial import AssetRepository, CommercialSolutionRepository
from app.schemas.commercial import CommercialSolutionCreate, CommercialSolutionUpdate
from app.services.audit import AuditService


class CommercialSolutionService:
    def __init__(self, session: Session):
        self.session = session
        self.solutions = CommercialSolutionRepository(session)
        self.generic_solutions = GenericSolutionRepository(session)
        self.assets = AssetRepository(session)
        self.audit = AuditService(session)

    def list_own(self, user: User) -> list[CommercialSolution]:
        return self.solutions.list_for_manufacturer(self._manufacturer_id(user))

    def create(self, user: User, dto: CommercialSolutionCreate) -> CommercialSolution:
        manufacturer_id = self._manufacturer_id(user)
        with transactional(self.session):
            if not self.generic_solutions.get(dto.generic_solution_id):
                raise EntityNotFound("Generic solution not found.")
            solution = CommercialSolution(
                manufacturer_id=manufacturer_id,
                generic_solution_id=dto.generic_solution_id,
                code=dto.code,
                name_es=dto.name_es,
                description=dto.description,
                technical_data=dto.technical_data,
                status=CommercialSolutionStatus.DRAFT,
                created_by=user.id,
                updated_by=user.id,
            )
            self.solutions.add(solution)
            self.session.flush()
            self.audit.record(
                actor_user_id=user.id,
                action="commercial_solution.created",
                entity_type="CommercialSolution",
                entity_id=solution.id,
            )
        return solution

    def get_own(self, user: User, solution_id: UUID) -> CommercialSolution:
        return self._owned_solution(user, solution_id)

    def update_own(
        self, user: User, solution_id: UUID, dto: CommercialSolutionUpdate
    ) -> CommercialSolution:
        with transactional(self.session):
            solution = self._owned_solution(user, solution_id)
            if solution.status == CommercialSolutionStatus.SUBMITTED:
                raise InvalidWorkflowTransition("Submitted solutions cannot be edited while under review.")
            if solution.status == CommercialSolutionStatus.ARCHIVED:
                raise InvalidWorkflowTransition("Archived solutions cannot be edited.")

            if solution.status in {
                CommercialSolutionStatus.APPROVED,
                CommercialSolutionStatus.REJECTED,
            }:
                solution.status = CommercialSolutionStatus.DRAFT
                solution.rejection_reason = None
                solution.approved_at = None
                solution.approved_by = None
                solution.submitted_at = None

            for field, value in dto.model_dump(exclude_unset=True).items():
                setattr(solution, field, value)
            solution.updated_by = user.id
            self.audit.record(
                actor_user_id=user.id,
                action="commercial_solution.updated",
                entity_type="CommercialSolution",
                entity_id=solution.id,
            )
        return solution

    def delete_own(self, user: User, solution_id: UUID) -> list[str]:
        with transactional(self.session):
            solution = self._owned_solution(user, solution_id, include_assets=True)
            if solution.status not in {CommercialSolutionStatus.DRAFT, CommercialSolutionStatus.REJECTED}:
                raise InvalidWorkflowTransition("Only draft or rejected solutions can be deleted.")
            asset_paths: list[str] = []
            assets = list(solution.assets)
            for asset in assets:
                solution.assets.remove(asset)
            self.session.flush()
            for asset in assets:
                if not self.assets.has_any_links(asset.id):
                    asset_paths.append(asset.relative_path)
                    self.assets.delete(asset)
            self.solutions.delete(solution)
            self.audit.record(
                actor_user_id=user.id,
                action="commercial_solution.deleted",
                entity_type="CommercialSolution",
                entity_id=solution_id,
            )
        return asset_paths

    def submit(self, user: User, solution_id: UUID) -> CommercialSolution:
        with transactional(self.session):
            solution = self._owned_solution(user, solution_id)
            if solution.status not in {
                CommercialSolutionStatus.DRAFT,
                CommercialSolutionStatus.REJECTED,
            }:
                raise InvalidWorkflowTransition("Only draft or rejected solutions can be submitted.")
            if not self.assets.has_valid_ifc_for_solution(solution.id):
                raise MissingIfcFile("A valid IFC asset is required before submission.")
            solution.status = CommercialSolutionStatus.SUBMITTED
            solution.rejection_reason = None
            solution.submitted_at = datetime.now(UTC)
            solution.updated_by = user.id
            self.audit.record(
                actor_user_id=user.id,
                action="commercial_solution.submitted",
                entity_type="CommercialSolution",
                entity_id=solution.id,
            )
        return solution

    def list_submitted_for_admin(self, user: User) -> list[CommercialSolution]:
        self._ensure_admin(user)
        return self.solutions.list_submitted()

    def approve(self, user: User, solution_id: UUID) -> CommercialSolution:
        self._ensure_admin(user)
        with transactional(self.session):
            solution = self._get(solution_id)
            if solution.status != CommercialSolutionStatus.SUBMITTED:
                raise InvalidWorkflowTransition("Only submitted solutions can be approved.")
            solution.status = CommercialSolutionStatus.APPROVED
            solution.rejection_reason = None
            solution.approved_at = datetime.now(UTC)
            solution.approved_by = user.id
            solution.updated_by = user.id
            self.audit.record(
                actor_user_id=user.id,
                action="commercial_solution.approved",
                entity_type="CommercialSolution",
                entity_id=solution.id,
            )
        return solution

    def reject(self, user: User, solution_id: UUID, *, reason: str) -> CommercialSolution:
        self._ensure_admin(user)
        with transactional(self.session):
            solution = self._get(solution_id)
            if solution.status != CommercialSolutionStatus.SUBMITTED:
                raise InvalidWorkflowTransition("Only submitted solutions can be rejected.")
            solution.status = CommercialSolutionStatus.REJECTED
            solution.rejection_reason = reason
            solution.approved_at = None
            solution.approved_by = None
            solution.updated_by = user.id
            self.audit.record(
                actor_user_id=user.id,
                action="commercial_solution.rejected",
                entity_type="CommercialSolution",
                entity_id=solution.id,
                context_data={"reason": reason},
            )
        return solution

    def _owned_solution(
        self, user: User, solution_id: UUID, *, include_assets: bool = False
    ) -> CommercialSolution:
        manufacturer_id = self._manufacturer_id(user)
        solution = self._get(solution_id, include_assets=include_assets)
        if solution.manufacturer_id != manufacturer_id:
            raise PermissionDenied("Commercial solution belongs to another manufacturer.")
        return solution

    def _manufacturer_id(self, user: User) -> UUID:
        if user.role != UserRole.MANUFACTURER or not user.manufacturer_id:
            raise PermissionDenied("Manufacturer access is required.")
        return user.manufacturer_id

    def _ensure_admin(self, user: User) -> None:
        if not is_admin(user.role):
            raise PermissionDenied("Administrator access is required.")

    def _get(self, solution_id: UUID, *, include_assets: bool = False) -> CommercialSolution:
        solution = self.solutions.get(solution_id, include_assets=include_assets)
        if not solution:
            raise EntityNotFound("Commercial solution not found.")
        return solution
