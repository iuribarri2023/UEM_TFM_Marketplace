from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFound, PermissionDenied, ValidationFailed
from app.core.permissions import UserRole
from app.db.models.commercial import Asset, User
from app.db.transaction import transactional
from app.infrastructure.bim.ifc import IfcOpenShellAdapter
from app.infrastructure.storage.local import LocalFileStorage, StagedFile, StoredFile
from app.repositories.commercial import AssetRepository, CommercialSolutionRepository
from app.services.audit import AuditService


class AssetService:
    def __init__(self, session: Session, storage: LocalFileStorage, bim_adapter: IfcOpenShellAdapter):
        self.session = session
        self.storage = storage
        self.bim_adapter = bim_adapter
        self.assets = AssetRepository(session)
        self.solutions = CommercialSolutionRepository(session)
        self.audit = AuditService(session)

    def upload_for_commercial_solution(
        self,
        *,
        user: User,
        solution_id: UUID,
        upload,
        role: str,
        asset_type: str,
        code: str | None = None,
    ) -> Asset:
        solution = self.solutions.get(solution_id)
        if not solution:
            raise EntityNotFound("Commercial solution not found.")
        if user.role != UserRole.MANUFACTURER or solution.manufacturer_id != user.manufacturer_id:
            raise PermissionDenied("Commercial solution belongs to another manufacturer.")
        if solution.status not in {"DRAFT", "REJECTED"}:
            raise ValidationFailed("Assets can only be changed on draft or rejected solutions.")

        staged: StagedFile | None = None
        stored: StoredFile | None = None
        try:
            staged = self.storage.stage_upload(upload)
            extraction_data = None
            validation_data = None
            if staged.format == "ifc":
                extraction_data = self.bim_adapter.inspect(self.storage.staged_absolute_path(staged))
                validation_data = {"valid": True, "validator": "ifcopenshell"}

            with transactional(self.session):
                stored = self.storage.promote(
                    staged,
                    folder=f"manufacturers/{solution.manufacturer_id}/solutions/{solution.id}",
                )
                asset = Asset(
                    code=code,
                    original_filename=stored.original_filename,
                    stored_filename=stored.stored_filename,
                    relative_path=stored.relative_path,
                    mime_type=stored.mime_type,
                    size=stored.size,
                    sha256=stored.sha256,
                    asset_type=asset_type,
                    format=stored.format,
                    role=role,
                    uploaded_by=user.id,
                    validation_data=validation_data,
                    extraction_data=extraction_data,
                )
                solution.assets.append(asset)
                self.assets.add(asset)
                self.session.flush()
                self.audit.record(
                    actor_user_id=user.id,
                    action="asset.uploaded",
                    entity_type="Asset",
                    entity_id=asset.id,
                    context_data={"commercial_solution_id": str(solution.id), "role": role},
                )
            return asset
        except Exception:
            if staged is not None:
                self.storage.discard_staged(staged)
            if stored is not None:
                self.storage.delete(stored.relative_path)
            raise

    def delete_from_commercial_solution(self, *, user: User, solution_id: UUID, asset_id: UUID) -> None:
        solution = self.solutions.get(solution_id, include_assets=True)
        if not solution:
            raise EntityNotFound("Commercial solution not found.")
        if user.role != UserRole.MANUFACTURER or solution.manufacturer_id != user.manufacturer_id:
            raise PermissionDenied("Commercial solution belongs to another manufacturer.")
        if solution.status not in {"DRAFT", "REJECTED"}:
            raise ValidationFailed("Assets can only be changed on draft or rejected solutions.")
        asset = next((item for item in solution.assets if item.id == asset_id), None)
        if asset is None:
            raise EntityNotFound("Asset not found for this commercial solution.")

        relative_path = asset.relative_path
        delete_physical = False
        with transactional(self.session):
            solution.assets.remove(asset)
            self.session.flush()
            if not self.assets.has_any_links(asset.id):
                self.assets.delete(asset)
                delete_physical = True
            self.audit.record(
                actor_user_id=user.id,
                action="asset.deleted" if delete_physical else "asset.detached",
                entity_type="Asset",
                entity_id=asset.id,
                context_data={"commercial_solution_id": str(solution.id)},
            )
        if delete_physical:
            self.storage.delete(relative_path)

    def list_for_commercial_solution(self, user: User, solution_id: UUID) -> list[Asset]:
        solution = self.solutions.get(solution_id)
        if not solution:
            raise EntityNotFound("Commercial solution not found.")
        if user.role == UserRole.ADMIN or solution.manufacturer_id == user.manufacturer_id:
            return self.assets.list_for_commercial_solution(solution_id)
        raise PermissionDenied("Commercial solution belongs to another manufacturer.")

    def get_downloadable_asset(self, user: User | None, asset_id: UUID) -> Asset:
        asset = self.assets.get(asset_id)
        if not asset:
            raise EntityNotFound("Asset not found.")

        if asset.generic_solutions:
            return asset

        if any(solution.status == "APPROVED" for solution in asset.commercial_solutions):
            return asset

        if user:
            if user.role == UserRole.ADMIN:
                return asset
            if user.role == UserRole.MANUFACTURER and user.manufacturer_id:
                if any(
                    solution.manufacturer_id == user.manufacturer_id
                    for solution in asset.commercial_solutions
                ):
                    return asset
        raise PermissionDenied("Asset access is forbidden.")
