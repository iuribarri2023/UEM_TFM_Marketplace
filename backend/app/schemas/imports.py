from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ImportModel(BaseModel):
    """Strict structural envelope for administrative file imports.

    Product-dependent technical content remains intentionally flexible inside
    the dedicated dict/list fields; unknown envelope keys are rejected so that
    typos do not silently disappear during import.
    """

    model_config = ConfigDict(extra="forbid")


class AssetImport(ImportModel):
    id: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=64)
    format: Literal["IFC", "PDF", "PNG", "JPG", "JPEG", "WEBP"]
    role: str = Field(min_length=1, max_length=64)
    uri: str = Field(min_length=1, max_length=512)

    @field_validator("uri")
    @classmethod
    def validate_relative_uri(cls, value: str) -> str:
        normalized = value.replace("\\", "/").strip()
        path = PurePosixPath(normalized)
        if not normalized or path.is_absolute() or ".." in path.parts:
            raise ValueError("Asset uri must be a safe relative path.")
        return normalized


class SlotImport(ImportModel):
    key: str = Field(min_length=1, max_length=64)
    name_es: str = Field(min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=64)
    sequence: int = Field(ge=0)
    required: bool = True
    properties: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] | None = None
    source_reference: dict[str, Any] | None = None


class CatalogueNodeImport(ImportModel):
    code: str = Field(min_length=1, max_length=64)
    name_es: str = Field(min_length=1, max_length=255)
    description: str | None = None


class GenericSolutionImport(ImportModel):
    code: str = Field(min_length=1, max_length=64)
    name_es: str = Field(min_length=1, max_length=255)
    description: str | None = None
    functional_unit: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=64)
    classifications: list[dict[str, Any]] = Field(default_factory=list)
    source_references: list[dict[str, Any]] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    slots: list[SlotImport] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    cte_compliance: dict[str, Any] = Field(default_factory=dict)
    environmental_data: dict[str, Any] = Field(default_factory=dict)
    economic_data: dict[str, Any] = Field(default_factory=dict)
    industrialization_data: dict[str, Any] = Field(default_factory=dict)
    viva_metrics: dict[str, Any] = Field(default_factory=dict)
    assets: list[AssetImport] = Field(
        min_length=1,
        json_schema_extra={
            "contains": {
                "type": "object",
                "required": ["format"],
                "properties": {"format": {"const": "IFC"}},
            }
        },
    )
    data_quality_notes: list[Any] | dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_assets(self) -> GenericSolutionImport:
        if not any(asset.format == "IFC" for asset in self.assets):
            raise ValueError("A generic solution import must reference at least one IFC asset.")
        ids = [asset.id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("Asset ids must be unique inside a generic solution.")
        return self


class GenericCatalogueImport(ImportModel):
    schema_version: str = Field(min_length=1)

    # Canonical document metadata. It is accepted/validated structurally but is
    # intentionally not copied into every GenericSolution database row.
    data_template: str | None = None
    property_dictionary: str | None = None
    regulatory_profile: str | None = None
    normalization_profile: str | None = None
    industrialization_profile: str | None = None
    generation_provenance: dict[str, Any] | None = None

    system: CatalogueNodeImport
    subsystem: CatalogueNodeImport
    archetype: CatalogueNodeImport
    generic_solutions: list[GenericSolutionImport] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_codes(self) -> GenericCatalogueImport:
        solution_codes = [item.code for item in self.generic_solutions]
        if len(solution_codes) != len(set(solution_codes)):
            raise ValueError("Generic solution codes must be unique inside an import document.")
        asset_ids = [asset.id for item in self.generic_solutions for asset in item.assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("Asset ids must be unique inside an import document.")
        return self


class ManufacturerImport(ImportModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    tax_id: str | None = Field(default=None, max_length=64)
    website: str | None = Field(default=None, max_length=512)
    description: str | None = None
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class ManufacturerSolutionImport(ImportModel):
    generic_solution_code: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    name_es: str = Field(min_length=1, max_length=255)
    description: str | None = None
    technical_data: dict[str, Any] = Field(default_factory=dict)
    status: Literal["DRAFT"] = "DRAFT"
    assets: list[AssetImport] = Field(
        min_length=1,
        json_schema_extra={
            "contains": {
                "type": "object",
                "required": ["format"],
                "properties": {"format": {"const": "IFC"}},
            }
        },
    )

    @model_validator(mode="after")
    def validate_assets(self) -> ManufacturerSolutionImport:
        if not any(asset.format == "IFC" for asset in self.assets):
            raise ValueError("A manufacturer solution import must reference at least one IFC asset.")
        ids = [asset.id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("Asset ids must be unique inside a manufacturer solution.")
        return self


class ManufacturerSolutionsImport(ImportModel):
    schema_version: str = Field(min_length=1)
    manufacturer: ManufacturerImport
    manufacturer_solutions: list[ManufacturerSolutionImport] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_codes(self) -> ManufacturerSolutionsImport:
        solution_codes = [item.code for item in self.manufacturer_solutions]
        if len(solution_codes) != len(set(solution_codes)):
            raise ValueError("Manufacturer solution codes must be unique inside an import document.")
        asset_ids = [asset.id for item in self.manufacturer_solutions for asset in item.assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("Asset ids must be unique inside an import document.")
        return self
