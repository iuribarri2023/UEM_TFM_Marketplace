from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.assets import AssetRead


class SystemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name_es: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class SubsystemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    system_id: UUID
    code: str
    name_es: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class ArchetypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subsystem_id: UUID
    code: str
    name_es: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class GenericSolutionSlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    name_es: str
    role: str | None
    sequence: int
    required: bool
    properties: dict[str, Any]
    metrics: dict[str, Any] | None
    source_reference: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class GenericSolutionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    archetype_id: UUID
    code: str
    name_es: str
    description: str | None
    functional_unit: str | None
    status: str | None
    classifications: list[dict[str, Any]]
    source_references: list[dict[str, Any]]
    attributes: dict[str, Any]
    metrics: dict[str, Any]
    cte_compliance: dict[str, Any]
    environmental_data: dict[str, Any]
    economic_data: dict[str, Any]
    industrialization_data: dict[str, Any]
    viva_metrics: dict[str, Any]
    data_quality_notes: list[Any] | dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class GenericSolutionRead(GenericSolutionSummary):
    slots: list[GenericSolutionSlotRead] = Field(default_factory=list)
    assets: list[AssetRead] = Field(default_factory=list)
