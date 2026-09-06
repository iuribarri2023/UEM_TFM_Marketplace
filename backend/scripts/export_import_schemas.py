from __future__ import annotations

import json
from pathlib import Path

from app.schemas.imports import GenericCatalogueImport, ManufacturerSolutionsImport


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "import"


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    schemas = {
        "generic_solutions.schema.json": GenericCatalogueImport.model_json_schema(),
        "manufacturer_solutions.schema.json": ManufacturerSolutionsImport.model_json_schema(),
    }
    for filename, schema in schemas.items():
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://avra-viva.local/schemas/import/{filename}"
        (SCHEMA_DIR / filename).write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(SCHEMA_DIR / filename)


if __name__ == "__main__":
    main()
