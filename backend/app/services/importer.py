from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidWorkflowTransition, ValidationFailed
from app.db.models.catalogue import Archetype, GenericSolution, GenericSolutionSlot, Subsystem, System
from app.db.models.commercial import Asset, CommercialSolution, Manufacturer
from app.db.transaction import transactional
from app.infrastructure.bim.ifc import IfcOpenShellAdapter
from app.infrastructure.storage.local import LocalFileStorage, StagedFile, StoredFile
from app.repositories.catalogue import (
    ArchetypeRepository,
    GenericSolutionRepository,
    GenericSolutionSlotRepository,
    SubsystemRepository,
    SystemRepository,
)
from app.repositories.commercial import AssetRepository, CommercialSolutionRepository, ManufacturerRepository
from app.schemas.imports import (
    AssetImport,
    GenericCatalogueImport,
    GenericSolutionImport,
    ManufacturerSolutionImport,
    ManufacturerSolutionsImport,
)


class _AssetImportMixin:
    session: Session
    storage: LocalFileStorage
    bim_adapter: IfcOpenShellAdapter
    assets: AssetRepository

    def _sync_assets(
        self,
        *,
        owner,
        asset_specs: list[AssetImport],
        source_root: Path,
        storage_folder: str,
        promoted_paths: list[str],
        delete_after_commit: list[str],
    ) -> int:
        desired_codes = {spec.id for spec in asset_specs}
        existing_by_code = {asset.code: asset for asset in list(owner.assets) if asset.code}

        for spec in asset_specs:
            source = self._resolve_source_asset(source_root, spec.uri)
            staged: StagedFile | None = None
            stored: StoredFile | None = None
            try:
                staged = self.storage.stage_local_file(source)
                if staged.format != spec.format.lower():
                    raise ValidationFailed(
                        f"Asset format mismatch for {spec.id}: JSON={spec.format}, file={staged.format}."
                    )

                extraction_data = None
                validation_data = None
                if staged.format == "ifc":
                    extraction_data = self.bim_adapter.inspect(self.storage.staged_absolute_path(staged))
                    validation_data = {"valid": True, "validator": "ifcopenshell"}

                asset = existing_by_code.get(spec.id) or self.assets.get_by_code(spec.id)
                if asset and asset not in owner.assets:
                    if asset.generic_solutions or asset.commercial_solutions:
                        raise ValidationFailed(
                            f"Asset code {spec.id} is already linked to another solution."
                        )
                    owner.assets.append(asset)

                if asset and asset.sha256 == staged.sha256:
                    self._update_asset_metadata(
                        asset,
                        spec=spec,
                        staged=staged,
                        validation_data=validation_data,
                        extraction_data=extraction_data,
                    )
                    self.storage.discard_staged(staged)
                    staged = None
                    continue

                stored = self.storage.promote(staged, folder=storage_folder)
                staged = None
                promoted_paths.append(stored.relative_path)

                if asset is None:
                    asset = Asset(code=spec.id)
                    self.assets.add(asset)
                    owner.assets.append(asset)
                elif asset.relative_path:
                    delete_after_commit.append(asset.relative_path)

                self._populate_asset_from_stored(
                    asset,
                    spec=spec,
                    stored=stored,
                    validation_data=validation_data,
                    extraction_data=extraction_data,
                )
                self.session.flush()
            finally:
                if staged is not None:
                    self.storage.discard_staged(staged)

        for asset in list(owner.assets):
            if asset.code and asset.code not in desired_codes:
                owner.assets.remove(asset)
                self.session.flush()
                if not self.assets.has_any_links(asset.id):
                    delete_after_commit.append(asset.relative_path)
                    self.assets.delete(asset)

        return len(asset_specs)

    @staticmethod
    def _resolve_source_asset(source_root: Path, uri: str) -> Path:
        root = source_root.resolve()
        path = (root / uri).resolve()
        if root != path and root not in path.parents:
            raise ValidationFailed(f"Asset uri escapes import directory: {uri}")
        if not path.is_file():
            raise ValidationFailed(f"Referenced asset does not exist: {uri}")
        return path

    @staticmethod
    def _update_asset_metadata(
        asset: Asset,
        *,
        spec: AssetImport,
        staged: StagedFile,
        validation_data: dict[str, Any] | None,
        extraction_data: dict[str, Any] | None,
    ) -> None:
        asset.original_filename = staged.original_filename
        asset.mime_type = staged.mime_type
        asset.size = staged.size
        asset.sha256 = staged.sha256
        asset.asset_type = spec.type
        asset.format = spec.format.lower()
        asset.role = spec.role
        asset.validation_data = validation_data
        asset.extraction_data = extraction_data

    @staticmethod
    def _populate_asset_from_stored(
        asset: Asset,
        *,
        spec: AssetImport,
        stored: StoredFile,
        validation_data: dict[str, Any] | None,
        extraction_data: dict[str, Any] | None,
    ) -> None:
        asset.code = spec.id
        asset.original_filename = stored.original_filename
        asset.stored_filename = stored.stored_filename
        asset.relative_path = stored.relative_path
        asset.mime_type = stored.mime_type
        asset.size = stored.size
        asset.sha256 = stored.sha256
        asset.asset_type = spec.type
        asset.format = stored.format
        asset.role = spec.role
        asset.validation_data = validation_data
        asset.extraction_data = extraction_data

    def _cleanup_failed_promotions(self, paths: list[str]) -> None:
        for relative_path in paths:
            self.storage.delete(relative_path)

    def _cleanup_replaced_files(self, paths: list[str]) -> None:
        for relative_path in set(paths):
            self.storage.delete(relative_path)


class CatalogImportService(_AssetImportMixin):
    def __init__(
        self,
        session: Session,
        storage: LocalFileStorage,
        bim_adapter: IfcOpenShellAdapter,
    ):
        self.session = session
        self.storage = storage
        self.bim_adapter = bim_adapter
        self.systems = SystemRepository(session)
        self.subsystems = SubsystemRepository(session)
        self.archetypes = ArchetypeRepository(session)
        self.solutions = GenericSolutionRepository(session)
        self.slots = GenericSolutionSlotRepository(session)
        self.assets = AssetRepository(session)

    def import_path(self, path: Path) -> dict[str, int]:
        files = self._discover_files(path)
        counts = {"files": 0, "generic_solutions": 0, "slots": 0, "assets": 0}
        for file_path in files:
            file_counts = self.import_file(file_path)
            counts["files"] += 1
            for key in ("generic_solutions", "slots", "assets"):
                counts[key] += file_counts[key]
        return counts

    def import_file(self, file_path: Path) -> dict[str, int]:
        payload = self._read_json(file_path, GenericCatalogueImport)
        promoted_paths: list[str] = []
        delete_after_commit: list[str] = []
        try:
            with transactional(self.session):
                counts = self._import_document(
                    payload,
                    source_root=file_path.parent,
                    promoted_paths=promoted_paths,
                    delete_after_commit=delete_after_commit,
                )
        except Exception:
            self._cleanup_failed_promotions(promoted_paths)
            raise
        self._cleanup_replaced_files(delete_after_commit)
        return counts

    def _import_document(
        self,
        payload: GenericCatalogueImport,
        *,
        source_root: Path,
        promoted_paths: list[str],
        delete_after_commit: list[str],
    ) -> dict[str, int]:
        system = self._upsert_system(payload.system.model_dump())
        subsystem = self._upsert_subsystem(payload.subsystem.model_dump(), system)
        archetype = self._upsert_archetype(payload.archetype.model_dump(), subsystem)

        solution_count = 0
        slot_count = 0
        asset_count = 0
        for solution_data in payload.generic_solutions:
            solution = self._upsert_solution(solution_data, archetype)
            slots = self._build_slots(solution, solution_data)
            self.slots.replace_for_solution(solution.id, slots)
            asset_count += self._sync_assets(
                owner=solution,
                asset_specs=solution_data.assets,
                source_root=source_root,
                storage_folder=f"generic-solutions/{solution.id}",
                promoted_paths=promoted_paths,
                delete_after_commit=delete_after_commit,
            )
            solution_count += 1
            slot_count += len(slots)
        return {
            "generic_solutions": solution_count,
            "slots": slot_count,
            "assets": asset_count,
        }

    def _upsert_system(self, data: dict[str, Any]) -> System:
        system = self.systems.get_by_code(data["code"]) or System(
            code=data["code"], name_es=data["name_es"]
        )
        system.name_es = data["name_es"]
        system.description = data.get("description")
        self.systems.add(system)
        self.session.flush()
        return system

    def _upsert_subsystem(self, data: dict[str, Any], system: System) -> Subsystem:
        subsystem = self.subsystems.get_by_code(data["code"]) or Subsystem(
            code=data["code"], name_es=data["name_es"], system_id=system.id
        )
        subsystem.system_id = system.id
        subsystem.name_es = data["name_es"]
        subsystem.description = data.get("description")
        self.subsystems.add(subsystem)
        self.session.flush()
        return subsystem

    def _upsert_archetype(self, data: dict[str, Any], subsystem: Subsystem) -> Archetype:
        archetype = self.archetypes.get_by_code(data["code"]) or Archetype(
            code=data["code"], name_es=data["name_es"], subsystem_id=subsystem.id
        )
        archetype.subsystem_id = subsystem.id
        archetype.name_es = data["name_es"]
        archetype.description = data.get("description")
        self.archetypes.add(archetype)
        self.session.flush()
        return archetype

    def _upsert_solution(
        self, data: GenericSolutionImport, archetype: Archetype
    ) -> GenericSolution:
        solution = self.solutions.get_by_code(data.code) or GenericSolution(
            code=data.code, name_es=data.name_es, archetype_id=archetype.id
        )
        solution.archetype_id = archetype.id
        solution.name_es = data.name_es
        solution.description = data.description
        solution.functional_unit = data.functional_unit
        solution.status = data.status
        solution.classifications = data.classifications
        solution.source_references = data.source_references
        solution.attributes = data.attributes
        solution.metrics = data.metrics
        solution.cte_compliance = data.cte_compliance
        solution.environmental_data = data.environmental_data
        solution.economic_data = data.economic_data
        solution.industrialization_data = data.industrialization_data
        solution.viva_metrics = data.viva_metrics
        solution.data_quality_notes = data.data_quality_notes
        self.solutions.add(solution)
        self.session.flush()
        return solution

    @staticmethod
    def _build_slots(
        solution: GenericSolution, data: GenericSolutionImport
    ) -> list[GenericSolutionSlot]:
        return [
            GenericSolutionSlot(
                generic_solution_id=solution.id,
                key=slot.key,
                name_es=slot.name_es,
                role=slot.role,
                sequence=slot.sequence,
                required=slot.required,
                properties=slot.properties,
                metrics=slot.metrics,
                source_reference=slot.source_reference,
            )
            for slot in data.slots
        ]

    @staticmethod
    def _discover_files(path: Path) -> list[Path]:
        if path.is_file():
            return [path]
        if not path.is_dir():
            raise ValidationFailed(f"Import path does not exist: {path}")
        return [
            item
            for item in sorted(path.glob("*.json"))
            if "obsolete" not in item.stem.lower() and not item.name.endswith(".schema.json")
        ]

    @staticmethod
    def _read_json(file_path: Path, model_type):
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
            return model_type.model_validate(raw)
        except json.JSONDecodeError as exc:
            raise ValidationFailed(f"Invalid JSON in {file_path.name}: {exc.msg}") from exc
        except ValidationError as exc:
            first = exc.errors(include_url=False)[0]
            location = ".".join(str(part) for part in first["loc"])
            raise ValidationFailed(
                f"Invalid import document {file_path.name} at {location}: {first['msg']}"
            ) from exc


class ManufacturerSolutionImportService(_AssetImportMixin):
    def __init__(
        self,
        session: Session,
        storage: LocalFileStorage,
        bim_adapter: IfcOpenShellAdapter,
    ):
        self.session = session
        self.storage = storage
        self.bim_adapter = bim_adapter
        self.manufacturers = ManufacturerRepository(session)
        self.generic_solutions = GenericSolutionRepository(session)
        self.solutions = CommercialSolutionRepository(session)
        self.assets = AssetRepository(session)

    def import_path(self, path: Path) -> dict[str, int]:
        files = CatalogImportService._discover_files(path)
        counts = {"files": 0, "manufacturers": 0, "manufacturer_solutions": 0, "assets": 0}
        for file_path in files:
            file_counts = self.import_file(file_path)
            counts["files"] += 1
            counts["manufacturers"] += file_counts["manufacturers"]
            counts["manufacturer_solutions"] += file_counts["manufacturer_solutions"]
            counts["assets"] += file_counts["assets"]
        return counts

    def import_file(self, file_path: Path) -> dict[str, int]:
        payload = CatalogImportService._read_json(file_path, ManufacturerSolutionsImport)
        promoted_paths: list[str] = []
        delete_after_commit: list[str] = []
        try:
            with transactional(self.session):
                manufacturer = self._upsert_manufacturer(payload)
                solution_count = 0
                asset_count = 0
                for data in payload.manufacturer_solutions:
                    solution = self._upsert_solution(data, manufacturer)
                    asset_count += self._sync_assets(
                        owner=solution,
                        asset_specs=data.assets,
                        source_root=file_path.parent,
                        storage_folder=(
                            f"manufacturers/{manufacturer.id}/solutions/{solution.id}"
                        ),
                        promoted_paths=promoted_paths,
                        delete_after_commit=delete_after_commit,
                    )
                    solution_count += 1
        except Exception:
            self._cleanup_failed_promotions(promoted_paths)
            raise
        self._cleanup_replaced_files(delete_after_commit)
        return {
            "manufacturers": 1,
            "manufacturer_solutions": solution_count,
            "assets": asset_count,
        }

    def _upsert_manufacturer(self, payload: ManufacturerSolutionsImport) -> Manufacturer:
        data = payload.manufacturer
        manufacturer = self.manufacturers.get_by_code(data.code) or Manufacturer(
            code=data.code, name=data.name
        )
        manufacturer.name = data.name
        manufacturer.tax_id = data.tax_id
        manufacturer.website = data.website
        manufacturer.description = data.description
        manufacturer.status = data.status
        self.manufacturers.add(manufacturer)
        self.session.flush()
        return manufacturer

    def _upsert_solution(
        self, data: ManufacturerSolutionImport, manufacturer: Manufacturer
    ) -> CommercialSolution:
        generic = self.generic_solutions.get_by_code(data.generic_solution_code)
        if generic is None:
            raise ValidationFailed(
                f"Generic solution does not exist: {data.generic_solution_code}. Import generic data first."
            )

        solution = self.solutions.get_by_code(data.code, include_assets=True)
        if solution and solution.manufacturer_id != manufacturer.id:
            raise ValidationFailed(
                f"Commercial solution code {data.code} already belongs to another manufacturer."
            )
        if solution and solution.status != "DRAFT":
            raise InvalidWorkflowTransition(
                f"Importer will not overwrite non-DRAFT commercial solution {data.code}."
            )
        if solution is None:
            solution = CommercialSolution(
                manufacturer_id=manufacturer.id,
                generic_solution_id=generic.id,
                code=data.code,
                name_es=data.name_es,
                status="DRAFT",
                technical_data={},
            )
        solution.manufacturer_id = manufacturer.id
        solution.generic_solution_id = generic.id
        solution.name_es = data.name_es
        solution.description = data.description
        solution.technical_data = data.technical_data
        solution.status = "DRAFT"
        solution.rejection_reason = None
        self.solutions.add(solution)
        self.session.flush()
        return solution
