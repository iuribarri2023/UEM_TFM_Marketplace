# Import JSON Schemas

The authoritative machine-readable schemas are:

- `generic_solutions.schema.json`
- `manufacturer_solutions.schema.json`

They use JSON Schema Draft 2020-12 and are generated from the Pydantic import contracts in `app/schemas/imports.py`.

Regenerate them after changing an import contract:

```bash
PYTHONPATH=. python scripts/export_import_schemas.py
```

Examples are available in `data/examples/`.
