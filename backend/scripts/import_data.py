from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import load_settings
from app.core.exceptions import ValidationFailed
from app.db.session import create_db_engine, create_session_factory
from app.infrastructure.bim.ifc import IfcOpenShellAdapter
from app.infrastructure.storage.local import LocalFileStorage
from app.schemas.imports import GenericCatalogueImport, ManufacturerSolutionsImport
from app.services.importer import CatalogImportService, ManufacturerSolutionImportService


def _validate_source_asset(root: Path, uri: str) -> Path:
    root = root.resolve()
    asset_path = (root / uri).resolve()
    if root != asset_path and root not in asset_path.parents:
        raise ValidationFailed(f"Asset uri escapes import directory: {uri}")
    if not asset_path.is_file():
        raise ValidationFailed(f"Referenced asset does not exist: {uri}")
    return asset_path


def validate_import_files(kind: str, path: Path) -> dict[str, int]:
    model_type = GenericCatalogueImport if kind == "generic" else ManufacturerSolutionsImport
    files = CatalogImportService._discover_files(path)
    bim = IfcOpenShellAdapter()
    result = {"files": 0, "solutions": 0, "assets": 0, "ifc_files": 0}

    for file_path in files:
        document = CatalogImportService._read_json(file_path, model_type)
        solutions = (
            document.generic_solutions
            if kind == "generic"
            else document.manufacturer_solutions
        )
        for solution in solutions:
            for asset in solution.assets:
                asset_path = _validate_source_asset(file_path.parent, asset.uri)
                if asset.format == "IFC":
                    bim.inspect(asset_path)
                    result["ifc_files"] += 1
                result["assets"] += 1
            result["solutions"] += 1
        result["files"] += 1
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate or import AVRA VIVA JSON bundles and their referenced assets."
    )
    parser.add_argument("kind", choices=("generic", "manufacturer"))
    parser.add_argument("path", type=Path, help="JSON file or directory of import JSON files")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate JSON, asset paths and IFC files without touching PostgreSQL or STORAGE_ROOT.",
    )
    args = parser.parse_args()

    if args.validate_only:
        print(json.dumps(validate_import_files(args.kind, args.path), indent=2))
        return

    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        storage = LocalFileStorage(settings.storage_root, settings.max_upload_size)
        bim = IfcOpenShellAdapter()

        with session_factory() as session:
            if args.kind == "generic":
                counts = CatalogImportService(session, storage, bim).import_path(args.path)
            else:
                counts = ManufacturerSolutionImportService(session, storage, bim).import_path(args.path)
        print(json.dumps(counts, indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
