from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.assets import AssetRead


class CommercialSolutionCreate(BaseModel):
    generic_solution_id: UUID
    code: str = Field(min_length=1, max_length=64)
    name_es: str = Field(min_length=1, max_length=255)
    description: str | None = None
    technical_data: dict[str, Any] = Field(default_factory=dict)


class CommercialSolutionUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name_es: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    technical_data: dict[str, Any] | None = None

    @model_validator(mode="after")
    def reject_null_required_values(self) -> CommercialSolutionUpdate:
        supplied = self.model_fields_set
        for field_name in ("code", "name_es", "technical_data"):
            if field_name in supplied and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null when supplied.")
        return self


class CommercialSolutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    manufacturer_id: UUID
    generic_solution_id: UUID
    code: str
    name_es: str
    description: str | None
    technical_data: dict[str, Any]
    status: str
    rejection_reason: str | None
    created_by: UUID | None
    updated_by: UUID | None
    submitted_at: datetime | None
    approved_at: datetime | None
    approved_by: UUID | None
    created_at: datetime
    updated_at: datetime
    assets: list[AssetRead] = Field(default_factory=list)


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class ManufacturerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    tax_id: str | None
    website: str | None
    description: str | None
    status: str
