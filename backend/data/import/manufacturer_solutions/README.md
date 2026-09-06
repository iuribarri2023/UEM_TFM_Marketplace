# Manufacturer solution imports

Place manufacturer/commercial solution JSON files in this directory.

Each JSON file must validate against:

`schemas/import/manufacturer_solutions.schema.json`

Asset `uri` values are resolved **relative to the JSON file**. A recommended layout is:

```text
manufacturer_solutions/
├── manufacturer-acme.json
└── assets/
    └── ifc/
        └── manufacturer/
            └── ACME-FAC-001.ifc
```

Commercial solutions imported by this administrative/offline loader are always `DRAFT`. Approval is deliberately not importable and must go through the application workflow.

Import generic solutions first, then run:

```bash
python scripts/import_data.py manufacturer data/import/manufacturer_solutions
```
