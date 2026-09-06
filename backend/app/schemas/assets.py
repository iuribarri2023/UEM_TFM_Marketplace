from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str | None
    original_filename: str
    mime_type: str
    size: int
    sha256: str
    asset_type: str
    format: str
    role: str
    uploaded_by: UUID | None
    validation_data: dict[str, Any] | None
    extraction_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
