# Importing Generic and Manufacturer Solutions

AVRA VIVA supports an administrative/offline import workflow for catalogue data and manufacturer products. The workflow is intentionally file-based so that JSON data can be reviewed/versioned and bundles can be imported reproducibly. IFC binaries are ignored by Git by default; use Git LFS or an artifact repository if you need to version them.

## Import folders

Use:

```text
data/import/
├── generic_solutions/
│   ├── *.json
│   └── assets/ifc/generic/*.ifc
└── manufacturer_solutions/
    ├── *.json
    └── assets/ifc/manufacturer/*.ifc
```

The `uri` of every asset is resolved relative to the JSON file containing it. Absolute paths and `..` traversal are rejected.

## Generic solution JSON

Validate against:

```text
schemas/import/generic_solutions.schema.json
```

A generic document contains one `system`, one `subsystem`, one `archetype`, and one or more `generic_solutions`. Each generic solution contains its stable fields, flexible JSON technical blocks, slots, and at least one referenced IFC asset.

The importer persists:

```text
System -> Subsystem -> Archetype -> GenericSolution -> GenericSolutionSlot
                                             |
                                             +-- Asset (through generic_solution_assets)
```

`classifications` and `source_references` are arrays. Product-dependent technical sections remain JSONB.

## Manufacturer solution JSON

Validate against:

```text
schemas/import/manufacturer_solutions.schema.json
```

A manufacturer import document contains the manufacturer organization and one or more commercial solutions. Each solution references an existing generic solution by `generic_solution_code`, contains flexible `technical_data`, and references at least one IFC.

The importer persists:

```text
Manufacturer -> CommercialSolution -> GenericSolution
                    |
                    +-- Asset (through commercial_solution_assets)
```

Manufacturer imports are restricted to `DRAFT`. They cannot bypass submission or administrator approval.

## IFC handling

For each referenced IFC the importer:

1. verifies the referenced path stays inside the JSON import directory;
2. stages the file in `STORAGE_ROOT/.staging`;
3. validates/opens it with IfcOpenShell;
4. extracts basic IFC metadata;
5. calculates SHA-256 and size;
6. moves it to the managed storage tree using a generated physical filename;
7. stores only metadata and the relative managed path in PostgreSQL.

If the database transaction fails, newly promoted files are removed. Re-importing the same functional asset code is idempotent and updates the existing asset rather than creating duplicates.

## Import order

Start PostgreSQL and apply migrations first:

```bash
docker compose up -d postgres
alembic upgrade head
```

Validate a bundle before touching the database (this also opens every referenced IFC with IfcOpenShell):

```bash
python scripts/import_data.py generic data/import/generic_solutions --validate-only
python scripts/import_data.py manufacturer data/import/manufacturer_solutions --validate-only
```

Import generic solutions:

```bash
python scripts/import_data.py generic data/import/generic_solutions
```

Then import manufacturer solutions:

```bash
python scripts/import_data.py manufacturer data/import/manufacturer_solutions
```

When running the backend through Docker Compose, `./data/import` is mounted read-only at `/app/data/import`, so the same administrative imports can be executed inside the application image:

```bash
docker compose run --rm backend python scripts/import_data.py generic data/import/generic_solutions
docker compose run --rm backend python scripts/import_data.py manufacturer data/import/manufacturer_solutions
```

A manufacturer solution whose `generic_solution_code` does not already exist is rejected.

## Examples

See:

```text
data/examples/generic_solutions.example.json
data/examples/manufacturer_solutions.example.json
```

Copy an example into the corresponding import folder, add the real IFC at the referenced relative URI, edit the data, validate against the schema, and run the import command.

## Contract reference

The JSON Schema files are authoritative for machine validation. The following is the intended human-readable contract.

### Generic solution bundle

Required document fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Version of the import document contract. |
| `system` | `{code, name_es, description?}` for the AVRA System. |
| `subsystem` | `{code, name_es, description?}` for the AVRA Subsystem. |
| `archetype` | `{code, name_es, description?}` for the AVRA Archetype. |
| `generic_solutions` | One or more solutions belonging to that archetype. |

The canonical metadata fields `data_template`, `property_dictionary`, `regulatory_profile`, `normalization_profile`, `industrialization_profile` and `generation_provenance` are accepted when present, but are document/import metadata and are not duplicated into each solution row.

Each `generic_solutions[]` item requires `code`, `name_es` and `assets`. `description`, `functional_unit`, `status`, `classifications`, `source_references`, `attributes`, `slots`, `metrics`, `cte_compliance`, `environmental_data`, `economic_data`, `industrialization_data`, `viva_metrics` and `data_quality_notes` are supported. Variable technical blocks remain JSONB so new construction-product families do not require a new SQL table for every property.

Each `slots[]` item has the stable envelope `key`, `name_es`, `role?`, `sequence`, `required`, `properties`, plus optional `metrics` and `source_reference`. Slot `key` is semantic and is not required to be unique inside one solution; database identity is a generated UUID.

### Manufacturer solution bundle

Required document fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Version of the import document contract. |
| `manufacturer` | Manufacturer organization (`code` and `name` required). |
| `manufacturer_solutions` | One or more commercial/manufacturer solutions. |

Optional manufacturer fields are `tax_id`, `website`, `description` and `status` (`ACTIVE` or `INACTIVE`).

Each `manufacturer_solutions[]` item requires:

- `generic_solution_code`: functional code of an already imported GenericSolution;
- `code`: globally unique commercial-solution functional code;
- `name_es`;
- `technical_data`: flexible manufacturer/product-specific JSON (defaults to `{}`);
- `status`: only `DRAFT` is accepted by file import;
- `assets`: one or more referenced files, including at least one IFC.

`description` is optional. The importer never accepts `manufacturer_id`, workflow approval fields, or database UUIDs from the JSON. Ownership is derived from the `manufacturer` block and database IDs are generated by the backend.

### Asset reference

Every `assets[]` entry has:

```json
{
  "id": "FAC-VEN-001-IFC",
  "type": "bim_model",
  "format": "IFC",
  "role": "primary_generic_model",
  "uri": "assets/ifc/generic/FAC-VEN-001.ifc"
}
```

`id` is the stable functional **asset code**, not the PostgreSQL UUID. It must be unique across imported assets. `uri` is a safe path relative to the JSON file. The file is copied into managed `STORAGE_ROOT`; the source path itself is never stored as the managed database path.

At least one `IFC` asset is mandatory for each imported generic or manufacturer solution in this import contract. IFC files are opened with IfcOpenShell before persistence. PostgreSQL stores file metadata, SHA-256, validation/extraction metadata and a managed relative path; file bytes remain on the filesystem.
