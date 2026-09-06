from __future__ import annotations

from uuid import UUID

from app.core.exceptions import ValidationFailed


def parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationFailed("Invalid UUID.") from exc
