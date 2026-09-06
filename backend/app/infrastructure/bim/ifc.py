from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.exceptions import InvalidIfcFile


class IfcOpenShellAdapter:
    """Validate and inspect IFC files using IfcOpenShell.

    IFC validity is a business prerequisite for submission, so the application
    does not silently fall back to string-based validation when IfcOpenShell is
    unavailable.
    """

    def inspect(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise InvalidIfcFile("IFC file does not exist.")
        try:
            import ifcopenshell  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise InvalidIfcFile(
                "IfcOpenShell is required to validate IFC files but is not installed."
            ) from exc

        try:
            model = ifcopenshell.open(str(path))
        except Exception as exc:
            raise InvalidIfcFile("IfcOpenShell could not open the IFC file.") from exc

        try:
            projects = model.by_type("IfcProject")
            project = projects[0] if projects else None
            entity_count = sum(1 for _ in model)
        except Exception as exc:
            raise InvalidIfcFile("IFC file could not be inspected safely.") from exc

        return {
            "valid": True,
            "validated_by": "ifcopenshell",
            "schema": getattr(model, "schema", None),
            "entity_count": entity_count,
            "project_name": getattr(project, "Name", None) if project else None,
            "project_global_id": getattr(project, "GlobalId", None) if project else None,
        }
