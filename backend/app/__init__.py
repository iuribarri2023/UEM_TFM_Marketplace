from __future__ import annotations

from typing import Any


def create_app(config: dict[str, Any] | None = None):
    """Create the Flask application without importing Flask at package import time."""
    from app.factory import create_app as _create_app

    return _create_app(config)


__all__ = ["create_app"]
