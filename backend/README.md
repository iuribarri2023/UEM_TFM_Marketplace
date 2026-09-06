# AVRA VIVA Marketplace Backend

Backend-only REST API for AVRA VIVA Marketplace. The application is a modular monolith built with Flask, SQLAlchemy 2.x and PostgreSQL. A separate frontend will consume `/api/v1`.

## Architecture

The application preserves the dependency flow:

```text
HTTP / Flask Blueprint
        ↓
Pydantic DTO
        ↓
Application Service
        ↓
Repository
        ↓
SQLAlchemy 2.x
        ↓
PostgreSQL
```

Core catalogue persistence is:

```text
System -> Subsystem -> Archetype -> GenericSolution -> GenericSolutionSlot
```

Technical data that varies by construction-product family is stored in JSONB. Assets are separate entities linked through `generic_solution_assets` and `commercial_solution_assets`; physical files live under `STORAGE_ROOT`.

## Requirements

- Python 3.12+
- PostgreSQL 16 recommended
- IfcOpenShell (installed as a project dependency)
- Docker / Docker Compose recommended for local PostgreSQL

## Local development

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d postgres postgres-test
alembic upgrade head
flask --app app:create_app run --debug
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
docker compose up -d postgres postgres-test
alembic upgrade head
flask --app app:create_app run --debug
```

Health check:

```bash
curl http://localhost:5000/health
```

## Importing GenericSolution + IFC data

The repository provides a controlled import workspace:

```text
data/import/generic_solutions/
├── *.json
└── assets/ifc/generic/*.ifc
```

JSON must conform to:

```text
schemas/import/generic_solutions.schema.json
```

Every imported GenericSolution must reference at least one IFC through its `assets` array. Asset `uri` paths are relative to the JSON file.

Validate first (JSON + paths + real IFC parse):

```bash
python scripts/import_data.py generic data/import/generic_solutions --validate-only
```

Import:

```bash
python scripts/import_data.py generic data/import/generic_solutions
```

The importer upserts System, Subsystem, Archetype and GenericSolution by functional code, replaces Slots for the solution, validates IFC using IfcOpenShell, manages the physical file, calculates SHA-256, and links the Asset through `generic_solution_assets`.

## Importing manufacturer/commercial solutions + IFC data

Use:

```text
data/import/manufacturer_solutions/
├── *.json
└── assets/ifc/manufacturer/*.ifc
```

JSON must conform to:

```text
schemas/import/manufacturer_solutions.schema.json
```

Import generic data first. Validate the manufacturer bundle:

```bash
python scripts/import_data.py manufacturer data/import/manufacturer_solutions --validate-only
```

Then import it:

```bash
python scripts/import_data.py manufacturer data/import/manufacturer_solutions
```

Manufacturer solutions reference an existing GenericSolution through `generic_solution_code`. Offline imports can only create/update `DRAFT` commercial solutions; submission and approval cannot be bypassed by importing JSON.

Detailed documentation and examples:

```text
docs/import-data.md
data/examples/generic_solutions.example.json
data/examples/manufacturer_solutions.example.json
```

When the repository is opened in VS Code, `.vscode/settings.json` associates the two import folders with their JSON Schemas so invalid fields and missing required structure are surfaced while editing.

## JSON Schema generation

The JSON Schema files are generated from the Pydantic import contracts in `app/schemas/imports.py`:

```bash
PYTHONPATH=. python scripts/export_import_schemas.py
```

## Initial users

After a manufacturer exists, create users from the CLI:

```bash
python scripts/create_user.py admin@example.com --role ADMIN
python scripts/create_user.py user@example.com --role MANUFACTURER --manufacturer-code MFR-001
```

Passwords are entered interactively and hashed with Argon2.

## Tests and quality checks

```bash
pytest
ruff check .
ruff format --check .
```

For PostgreSQL tests:

Linux/macOS:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://avra:avra@localhost:5433/avra_viva_test
pytest
```

PowerShell:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://avra:avra@localhost:5433/avra_viva_test"
pytest
```

The integration suite includes a migration-from-empty-database test.

## API surface

Catalogue/public:

```text
GET /health
GET /api/v1/systems
GET /api/v1/subsystems
GET /api/v1/archetypes
GET /api/v1/generic-solutions
GET /api/v1/generic-solutions/{id}
GET /api/v1/manufacturers
GET /api/v1/manufacturers/{id}
GET /api/v1/marketplace/commercial-solutions
GET /api/v1/marketplace/commercial-solutions/{id}
GET /api/v1/assets/{id}/download
```

Authentication/manufacturer/admin endpoints are organized under `/api/v1/auth`, `/api/v1/manufacturer` and `/api/v1/admin`.

## Production notes

- `APP_ENV=production` requires an explicit `DATABASE_URL` and refuses the development JWT secret or any JWT secret shorter than 32 bytes.
- CORS origins are configured through `CORS_ORIGINS`.
- File bytes are never stored in PostgreSQL.
- Physical paths are generated by the backend and only relative paths are persisted.
- IFC submission requires successful IfcOpenShell validation.
- Docker runs the application as a non-root user.

## Scope

The repository intentionally remains a modular monolith. It does not introduce Kubernetes, Redis, Kafka, RabbitMQ, GraphQL, Elasticsearch, CQRS or event sourcing without a concrete requirement.
