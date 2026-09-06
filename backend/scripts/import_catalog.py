"""Backward-compatible wrapper for generic catalogue imports."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import load_settings
from app.db.session import create_db_engine, create_session_factory
from app.infrastructure.bim.ifc import IfcOpenShellAdapter
from app.infrastructure.storage.local import LocalFileStorage
from app.services.importer import CatalogImportService


def main() -> None:
    parser = argparse.ArgumentParser(description="Import canonical AVRA generic-solution JSON.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    settings = load_settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)
    storage = LocalFileStorage(settings.storage_root, settings.max_upload_size)
    try:
        with session_factory() as session:
            counts = CatalogImportService(
                session, storage, IfcOpenShellAdapter()
            ).import_path(args.path)
        print(counts)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
