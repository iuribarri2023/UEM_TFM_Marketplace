# AVRA VIVA Marketplace Backend — Codex Instructions

## 1. Project scope

This repository contains the **backend only** for AVRA VIVA Marketplace.

AVRA VIVA Marketplace is a platform for consulting, managing and publishing generic and commercial construction solutions associated with BIM/IFC models.

A separate web frontend will be developed later.

The frontend will consume this backend exclusively through a versioned REST API.

Do not implement frontend code in this repository.

Do not introduce:

* React;
* Vue;
* Angular;
* Next.js;
* frontend templates;
* server-side rendered application pages;
* frontend-specific business logic.

The frontend/backend integration boundary is:

```text
/api/v1
```

The backend must remain independent from the future frontend technology.

---

## 2. Architectural source of truth

Before making architectural or structural changes, read:

```text
AGENTS.md
ARCHITECTURE.md
docs/backend-specification.md
```

Also inspect the current canonical AVRA JSON examples when working on the GenericSolution data model or catalogue import.

Prefer the latest schema-versioned JSON examples.

Do not use files explicitly marked as obsolete as the authoritative representation when current equivalents exist.

If instructions conflict, use this precedence:

1. explicit user instructions for the current task;
2. AGENTS.md;
3. ARCHITECTURE.md;
4. backend-specification.md.

Do not silently introduce a different architecture.

---

# 3. Architectural style

The backend is a:

```text
Modular Monolith
+
REST API
+
PostgreSQL
+
Filesystem storage
```

It is intentionally not a microservice architecture.

The application must remain:

```text
simple
explicit
modular
testable
portable
maintainable
```

Do not overengineer the PoC.

---

# 4. Fundamental dependency direction

The expected application flow is:

```text
HTTP Request
    ↓
Flask Blueprint
    ↓
Pydantic DTO
    ↓
Application Service
    ↓
Repository
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

Conceptually:

```text
HTTP / API
    ↓
Application
    ↓
Domain
    ↓
Persistence abstractions
    ↓
Infrastructure
```

Dependencies should point inward.

Framework and infrastructure details must not leak into application/domain rules.

---

# 5. Flask responsibilities

Flask is the HTTP adapter.

Blueprints may:

* define routes;
* read path parameters;
* read query parameters;
* read request bodies;
* obtain authentication context;
* validate API input with Pydantic;
* invoke Application Services;
* serialize responses;
* map semantic exceptions to HTTP responses.

Blueprints must NOT:

* contain business rules;
* contain workflow transitions;
* perform SQLAlchemy queries;
* access PostgreSQL directly;
* call `session.commit()`;
* manipulate storage directly;
* invoke IfcOpenShell directly;
* implement ownership rules directly;
* return internal persistence objects as API contracts.

Keep controllers thin.

---

# 6. Application Services

Application Services implement use cases.

Examples include:

```text
CatalogService
GenericSolutionService
AuthenticationService
CommercialSolutionService
ApprovalService
AssetService
BimService
CatalogImportService
```

Services coordinate:

* domain rules;
* permissions;
* repositories;
* transaction boundaries;
* storage adapters;
* BIM adapters;
* auditing when introduced.

Application Services must not depend on Flask.

Do not import:

```python
flask
flask.request
flask.current_app
flask.jsonify
```

inside services or domain code.

A use case should remain callable from:

```text
REST API
CLI
scripts
tests
```

without duplicating business logic.

---

# 7. Domain layer

The domain represents business concepts and rules.

Initial important concepts include:

```text
System
Subsystem
Archetype
GenericSolution
GenericSolutionSlot
```

Future concepts include:

```text
Manufacturer
User
CommercialSolution
Asset
Approval workflow
```

The domain must remain reasonably independent from Flask, HTTP and persistence technology.

Use semantic exceptions rather than HTTP-specific behavior.

Examples:

```text
EntityNotFound
PermissionDenied
InvalidWorkflowTransition
ValidationError
MissingIfcFile
InvalidIfcFile
DuplicateCode
```

The API layer maps these exceptions to HTTP status codes.

Avoid excessively academic DDD.

---

# 8. Repository pattern

Database operations belong in repositories.

Application Services call repositories instead of using SQLAlchemy queries directly.

Repositories may:

* build SQLAlchemy queries;
* retrieve records;
* persist records;
* remove records;
* perform persistence-specific filtering.

Repositories must not:

* import Flask;
* return Flask responses;
* implement authorization;
* implement application workflows;
* independently control commits.

Do not scatter:

```python
session.commit()
```

across repositories.

---

# 9. Transactions

SQLAlchemy sessions and transactions must be explicit.

Conceptual lifecycle:

```text
HTTP Request
    ↓
SQLAlchemy Session
    ↓
Application Service
    ↓
Repositories
    ↓
commit / rollback
    ↓
close
```

Prefer one transaction boundary per application use case.

Repositories normally perform persistence operations against an existing Session.

Application Services or a simple Unit of Work control commit/rollback.

Do not introduce a complex Unit of Work abstraction unless it provides real value.

---

# 10. SQLAlchemy

Use:

```text
SQLAlchemy 2.x
```

directly.

Do not use Flask-SQLAlchemy as the architectural foundation.

Prefer:

* modern declarative mappings;
* typed mappings;
* explicit relationships;
* explicit indexes and constraints;
* PostgreSQL-native types where appropriate.

SQLAlchemy models are persistence models.

They are not the public REST API contract.

---

# 11. PostgreSQL

PostgreSQL is the primary database.

Use appropriate types:

```text
UUID
VARCHAR
TEXT
BOOLEAN
INTEGER
TIMESTAMPTZ
JSONB
FOREIGN KEY
UNIQUE
CHECK
INDEX
```

Database identities should normally use UUID.

AVRA codes are functional identifiers and must remain separate from UUID primary keys.

Example:

```text
id   = UUID(...)
code = FAC-VEN-001
```

Do not use functional AVRA codes as primary keys.

---

# 12. Hybrid relational + JSONB modelling

The catalogue uses a hybrid relational/JSONB model.

Use relational modelling for:

* identity;
* taxonomy;
* parent-child relationships;
* ordering;
* lifecycle fields;
* fields that are stable across all product categories.

Use JSONB for technical information whose internal structure legitimately varies between construction-product categories.

Do not model the complete catalogue as JSON.

Do not flatten every observed technical property into SQL columns.

Do not create different database schemas for each construction-product family.

---

# 13. Core catalogue hierarchy

The initial catalogue hierarchy is:

```text
System
    ↓
Subsystem
    ↓
Archetype
    ↓
GenericSolution
    ↓
GenericSolutionSlot
```

Relationships:

```text
System
  └── Subsystem
        └── Archetype
              └── GenericSolution
                    └── GenericSolutionSlot
```

One System has many Subsystems.

One Subsystem belongs to one System.

One Subsystem has many Archetypes.

One Archetype belongs to one Subsystem.

One Archetype has many GenericSolutions.

One GenericSolution belongs to one Archetype.

One GenericSolution has zero or many GenericSolutionSlots.

One GenericSolutionSlot belongs to exactly one GenericSolution.

---

# 14. System

Initial persistent fields:

```text
id
code
name_es
description
created_at
updated_at
```

Rules:

* `id` is UUID primary key;
* `code` is a unique functional identifier;
* `name_es` is required.

---

# 15. Subsystem

Initial persistent fields:

```text
id
system_id
code
name_es
description
created_at
updated_at
```

`system_id` is a foreign key to `systems.id`.

---

# 16. Archetype

Initial persistent fields:

```text
id
subsystem_id
code
name_es
description
created_at
updated_at
```

`subsystem_id` is a foreign key to `subsystems.id`.

---

# 17. GenericSolution

GenericSolution represents a generic/reference construction solution.

It is independent of a manufacturer.

Recommended initial persistence model:

```text
generic_solutions
-----------------

id UUID PRIMARY KEY

archetype_id UUID NOT NULL

code VARCHAR NOT NULL UNIQUE

name_es VARCHAR NOT NULL

description TEXT NULL

functional_unit VARCHAR NULL

status VARCHAR NULL

classifications JSONB NOT NULL

source_references JSONB NOT NULL

attributes JSONB NOT NULL

metrics JSONB NOT NULL

cte_compliance JSONB NOT NULL

environmental_data JSONB NOT NULL

economic_data JSONB NOT NULL

industrialization_data JSONB NOT NULL

viva_metrics JSONB NOT NULL

data_quality_notes JSONB NULL

created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Use suitable empty defaults where appropriate.

Do not create `created_by` / `updated_by` foreign keys to fake users before the User entity exists.

Those fields may be introduced later with authentication/auditing.

---

# 18. GenericSolution JSONB sections

The canonical catalogue contains semantically distinct blocks.

Keep them distinct rather than collapsing everything into one `technical_data` object.

Expected blocks include:

```text
classifications
source_references
attributes
metrics
cte_compliance
environmental_data
economic_data
industrialization_data
viva_metrics
data_quality_notes
```

These blocks differ substantially between:

* façades;
* roofs;
* windows;
* future construction systems.

Do not create dedicated SQL columns for every internal key.

The JSONB structures must preserve valid keys that are specific to one product family.

---

# 19. GenericSolutionSlot is a first-class entity

Slots are part of the initial persistence model.

They are not deferred to a future phase.

Recommended table:

```text
generic_solution_slots
----------------------

id UUID PRIMARY KEY

generic_solution_id UUID NOT NULL

key VARCHAR NOT NULL

name_es VARCHAR NOT NULL

role VARCHAR NULL

sequence INTEGER NOT NULL

required BOOLEAN NOT NULL DEFAULT TRUE

properties JSONB NOT NULL

metrics JSONB NULL

source_reference JSONB NULL

created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

`generic_solution_id` references:

```text
generic_solutions.id
```

Prefer:

```text
ON DELETE CASCADE
```

because Slots are composition children of their GenericSolution.

---

# 20. Slot identity

`GenericSolutionSlot.id` is the database identity.

Do NOT use:

```text
slot.key
```

as a primary key.

Do NOT create:

```text
UNIQUE(generic_solution_id, key)
```

A single GenericSolution may legitimately contain multiple Slots having the same key.

For example, a construction system may contain multiple thermal insulation positions sharing the same semantic key but with different sequence positions and different properties.

`key` is semantic.

UUID is identity.

---

# 21. Slot ordering

`sequence` controls the intended order of Slots inside a GenericSolution.

Create an index suitable for:

```text
generic_solution_id + sequence
```

Do not necessarily require sequence to be unique unless the canonical data guarantees it.

If duplicate sequence values exist, repositories/services should use deterministic secondary ordering.

---

# 22. Slot properties

Technical properties belonging to a Slot vary significantly depending on the product.

Examples include:

```text
material_family
product_family
thickness
thermal_conductivity
thermal_resistance
reaction_to_fire
support_system
frame_depth
stud_spacing
opening_type
glazing configuration
waterproofing system
slope
structural support
```

Store these in:

```text
properties JSONB
```

Do not create one database column for every possible technical property.

---

# 23. Do not use EAV for current Slot properties

Do not implement the current Slot property model as:

```text
slot_attributes
---------------
slot_id
attribute_key
data_type
unit
value
```

unless a future concrete requirement makes this necessary.

The canonical representation uses nested property objects and should remain compatible with that model.

Avoid EAV complexity for the PoC.

---

# 24. Slot metrics

Slots may optionally contain their own metrics.

Examples include window frame or glazing performance.

Support:

```text
metrics JSONB NULL
```

Do not assume all Slots have metrics.

Do not confuse:

```text
GenericSolution.metrics
```

with:

```text
GenericSolutionSlot.metrics
```

Solution-level and component-level performance are different concepts.

---

# 25. Slot source references

Some Slots may contain their own provenance/source information.

Support:

```text
source_reference JSONB NULL
```

This is distinct from:

```text
GenericSolution.source_references
```

Do not normalize source/provenance metadata into a complex relational model during the initial implementation.

---

# 26. Product-family independence

The database architecture must NOT assume that every GenericSolution is:

* a façade;
* a roof;
* a window;
* layered;
* measured in m²;
* composed of insulation;
* composed exclusively of physical layers.

Slots may represent:

* layers;
* components;
* assemblies;
* subassemblies;
* functional positions;
* frames;
* glazing;
* equipment subsystems;
* replaceable technical components.

The same model must be able to evolve toward additional construction products such as:

```text
doors
partitions
floors
structural systems
heat pumps
HVAC systems
ventilation systems
photovoltaic systems
other construction products
```

Do not implement those categories now.

Do not create category-specific SQL tables for them.

---

# 27. Example generic model

The following are all valid with the same database structure.

Facade:

```text
GenericSolution
    ├── exterior finish
    ├── cavity
    ├── insulation
    ├── main leaf
    └── internal finish
```

Roof:

```text
GenericSolution
    ├── protection
    ├── separation layer
    ├── waterproofing
    ├── insulation
    ├── slope formation
    └── structural support
```

Window:

```text
GenericSolution
    ├── frame
    └── glazing
```

Do not encode one of these topologies into the schema itself.

---

# 28. Pydantic

Use:

```text
Pydantic 2.x
```

for API/application DTOs.

Keep separate:

```text
HTTP JSON
Pydantic DTO
Application/domain data
SQLAlchemy model
```

Do not expose SQLAlchemy models directly as REST responses.

Generic DTOs should be able to represent different product categories without one Pydantic schema per archetype.

Avoid:

```text
FacadeGenericSolutionDTO
RoofGenericSolutionDTO
WindowGenericSolutionDTO
```

unless future validation requirements genuinely justify them.

---

# 29. Canonical JSON mapping

Conceptually:

```text
JSON system
    -> System

JSON subsystem
    -> Subsystem

JSON archetype
    -> Archetype

generic_solutions[]
    -> GenericSolution

generic_solutions[].slots[]
    -> GenericSolutionSlot
```

GenericSolution nested mappings:

```text
classifications
    -> JSONB

source_references
    -> JSONB

attributes
    -> JSONB

metrics
    -> JSONB

cte_compliance
    -> JSONB

environmental_data
    -> JSONB

economic_data
    -> JSONB

industrialization_data
    -> JSONB

viva_metrics
    -> JSONB

data_quality_notes
    -> JSONB
```

GenericSolutionSlot mappings:

```text
properties
    -> JSONB

metrics
    -> JSONB

source_reference
    -> JSONB
```

---

# 30. Import metadata

Top-level source-generation metadata such as:

```text
schema_version
data_template
property_dictionary
generation_provenance
normalization_profile
industrialization_profile
```

does not automatically belong to the GenericSolution SQL business model.

Do not blindly copy all document-level metadata into every GenericSolution.

Importer-level provenance may later belong to:

```text
ImportBatch
ImportRun
Audit metadata
```

if a concrete requirement appears.

Do not overdesign it in the initial implementation.

---

# 31. Classifications

Keep initial classification information in:

```text
GenericSolution.classifications JSONB
```

Classification systems can vary.

Examples may include:

```text
CTE-CEC
IVE-BDC
IFC
future classification systems
```

Do not create an extensive classification subsystem in the initial PoC.

Normalization may be revisited if classification queries become important.

---

# 32. Economic information

Keep the complete economic block in:

```text
economic_data JSONB
```

Do not reduce it to only:

```text
unit_cost
```

The canonical model may contain:

* currency;
* functional unit;
* unit cost;
* source;
* scope;
* BC3 decomposition;
* source observations;
* status;
* notes.

Do not normalize BC3 decomposition into relational entities during the initial implementation.

Revisit this only if independent analytics/querying over decomposition items becomes a real use case.

---

# 33. Environmental information

Keep environmental information in:

```text
environmental_data JSONB
```

Do not reduce environmental information to one fixed GWP column.

Preserve:

* values;
* units;
* aggregation;
* observations;
* sources;
* status;
* component breakdowns when present.

---

# 34. Industrialization information

Keep:

```text
industrialization_data JSONB
viva_metrics JSONB
```

as variable structured data.

Do not prematurely normalize these structures.

---

# 35. Null values

The canonical catalogue intentionally distinguishes between:

```text
known value
unknown/unavailable value
status describing why it is unavailable
```

Do not convert null technical values to zero.

Do not invent missing values.

Do not infer one solution's missing technical properties from neighboring solutions during persistence.

Persistence should preserve source semantics.

---

# 36. Assets

Assets will eventually become first-class relational entities.

Do not permanently embed file handling into GenericSolution.

Future architecture:

```text
GenericSolution
    ↓
Asset relation
    ↓
Asset
    ↓
FileStorage
```

Do not implement file uploads or FileStorage during the initial catalogue foundation unless explicitly requested.

Do not store IFC/PDF/image bytes in PostgreSQL.

---

# 37. File storage

When introduced, files live outside PostgreSQL.

PostgreSQL stores metadata and relative paths.

Use a storage abstraction:

```text
FileStorage
```

Initial implementation:

```text
LocalFileStorage
```

Possible future implementations:

```text
S3FileStorage
AzureBlobStorage
MinIOFileStorage
```

The application/domain must not depend on absolute storage paths.

---

# 38. BIM integration

IfcOpenShell must eventually be isolated behind:

```text
BimService
```

and an infrastructure adapter.

Conceptually:

```text
Application Service
    ↓
BimService
    ↓
IfcOpenShellAdapter
```

Do not call IfcOpenShell directly from Flask Blueprints.

Do not implement BIM processing before its phase unless explicitly requested.

---

# 39. Authentication and authorization

Authentication will be implemented later.

Expected approach:

```text
JWT access token
JWT refresh token
Argon2 or bcrypt
```

Backend authorization is always authoritative.

Never rely on the future frontend for security enforcement.

---

# 40. Future CommercialSolution

Future commercial solutions will belong to Manufacturers and reference a GenericSolution.

Conceptually:

```text
GenericSolution
       ↑
       |
CommercialSolution
       |
       ↓
Manufacturer
```

Do not implement CommercialSolution in the initial catalogue foundation unless explicitly requested.

The current GenericSolution model must not make future commercial-product support difficult.

---

# 41. API conventions

Main API prefix:

```text
/api/v1
```

Operational endpoint:

```text
GET /health
```

Success format should generally follow:

```json
{
  "data": {}
}
```

Errors should generally follow:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message."
  }
}
```

Do not expose:

* Python stack traces;
* absolute filesystem paths;
* SQL details;
* internal exceptions.

---

# 42. Future frontend integration

The frontend will communicate only through REST.

Conceptually:

```text
Web Frontend
     |
     | HTTPS / JSON
     v
REST API /api/v1
     |
     v
Application Services
     |
     v
Domain / Persistence
```

The frontend must not:

* access PostgreSQL directly;
* access filesystem paths directly;
* depend on SQLAlchemy models;
* depend on Python exceptions;
* enforce backend permissions on behalf of the backend.

Keep API contracts frontend-agnostic.

---

# 43. OpenAPI

The REST API is a contract with the future frontend.

The architecture must support explicit OpenAPI documentation.

A manually maintained:

```text
openapi.yaml
```

is acceptable initially.

Do not restructure domain/application code around a particular Flask OpenAPI extension.

---

# 44. CORS

Future frontend origins must be configurable through:

```text
CORS_ORIGINS
```

Do not hardcode frontend URLs in application logic.

Do not use unrestricted CORS in production.

---

# 45. Configuration

Use environment variables for environment-dependent configuration.

Expected variables include:

```text
APP_ENV
DATABASE_URL
JWT_SECRET_KEY
STORAGE_ROOT
MAX_UPLOAD_SIZE
CORS_ORIGINS
```

Support:

```text
development
testing
production
```

Never commit real secrets.

Provide:

```text
.env.example
```

Do not commit `.env`.

---

# 46. Alembic

Use Alembic from the first database implementation.

Database changes follow:

```text
SQLAlchemy model
    ↓
Alembic migration
    ↓
migration review
    ↓
apply migration
```

Never use production `create_all()` as the schema evolution mechanism.

---

# 47. Initial indexes

At minimum consider indexes for:

```text
systems.code

subsystems.system_id
subsystems.code

archetypes.subsystem_id
archetypes.code

generic_solutions.archetype_id
generic_solutions.code

generic_solution_slots.generic_solution_id
generic_solution_slots(generic_solution_id, sequence)
generic_solution_slots(generic_solution_id, key)
```

Do not add GIN indexes to JSONB indiscriminately.

Add JSONB indexes only when concrete query patterns justify them.

---

# 48. Testing

Use:

```text
pytest
```

Test structure:

```text
tests/unit
tests/integration
tests/api
```

Unit tests cover:

* Application Services;
* domain rules;
* workflow;
* permissions.

Integration tests cover:

* repositories;
* PostgreSQL;
* FileStorage when introduced;
* BIM adapters when introduced.

API tests cover:

* routes;
* validation;
* status codes;
* serialization;
* authentication when introduced.

---

# 49. GenericSolution/Slot tests

The initial catalogue model should prove that the generalized schema can store representative:

```text
facade
roof
window
```

solutions.

Tests must verify at least:

* GenericSolution JSONB round-trip;
* Slot properties JSONB round-trip;
* optional Slot metrics;
* optional Slot source_reference;
* ordering by `sequence`;
* multiple Slots per solution;
* duplicate Slot keys within one GenericSolution;
* different technical properties across different construction categories without schema changes.

Do not require the complete production JSON files in every unit test.

Use small representative fixtures.

Integration tests involving JSONB should use PostgreSQL rather than pretending SQLite is equivalent.

---

# 50. Application Factory

Flask must use:

```python
create_app()
```

Do not create a giant `app.py`.

The factory assembles:

* configuration;
* Blueprints;
* error handlers;
* database infrastructure.

Business logic remains outside the factory.

---

# 51. Health endpoint

Expose:

```text
GET /health
```

Initial response:

```json
{
  "status": "ok"
}
```

Keep it simple.

Readiness/liveness checks may be introduced later.

---

# 52. Development tooling

Use:

```text
Python 3.12+
pytest
ruff
```

Configure tooling through:

```text
pyproject.toml
```

Run, where available:

```bash
pytest
ruff check .
ruff format --check .
```

Do not claim checks passed unless they actually ran.

---

# 53. Docker

Use Docker Compose initially for PostgreSQL.

A backend service may also be included if useful.

Use persistent volumes.

Do not store persistent PostgreSQL data only inside ephemeral container layers.

Do not introduce Kubernetes.

---

# 54. Security baseline

Never:

* commit secrets;
* expose stack traces;
* trust frontend ownership information;
* use user-controlled filesystem paths directly;
* bypass authorization because the frontend hides functionality;
* expose internal database information.

Upload security will be implemented when Assets/FileStorage are introduced.

---

# 55. Things that must NOT be introduced initially

Do not introduce without a concrete requirement:

```text
Microservices
Kubernetes
Kafka
RabbitMQ
Event sourcing
CQRS
GraphQL
Elasticsearch
Redis
S3
distributed BIM processing
advanced workflow engines
advanced versioning
one table per archetype
one table per product family
one table per Slot type
EAV Slot property model
BLOB/BYTEA IFC storage
```

---

# 56. Future Java portability

Maintain conceptual portability toward Spring Boot:

```text
Python                         Java

Flask Blueprint               @RestController
Pydantic DTO                  DTO / Java Record
Application Service           @Service
Repository                    Repository
SQLAlchemy                    JPA / Hibernate
Alembic                       Flyway / Liquibase
JWT                           Spring Security
FileStorage                   StorageService
BimService                    BIM adapter/service
```

Do not write Java-style Python unnecessarily.

Architectural equivalence matters more than syntactic imitation.

---

# 57. Project structure

Target structure:

```text
backend/

├── app/
│   ├── __init__.py
│   ├── factory.py
│
│   ├── api/
│   │   └── v1/
│
│   ├── domain/
│
│   ├── services/
│
│   ├── repositories/
│
│   ├── db/
│   │   ├── models/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── transaction.py
│
│   ├── schemas/
│
│   ├── infrastructure/
│   │   ├── storage/
│   │   └── bim/
│
│   └── core/
│       ├── config.py
│       ├── security.py
│       ├── permissions.py
│       ├── exceptions.py
│       └── logging.py
│
├── migrations/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
├── storage/
├── docs/
│
├── alembic.ini
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── AGENTS.md
├── ARCHITECTURE.md
└── README.md
```

Do not create meaningless placeholder code merely to reproduce this tree.

---

# 58. Development sequence

Current intended sequence:

```text
Phase 1
Backend foundation
+
initial GenericSolution/Slot persistence foundation

Phase 2
Generic catalogue API

Phase 3
Catalogue importer

Phase 4
Manufacturers + authentication

Phase 5
Commercial solutions

Phase 6
Assets

Phase 7
BIM

Phase 8
Approval workflow
```

Do not implement future phases prematurely.

---

# 59. Change discipline

For every task:

1. read the relevant architecture/specification;
2. inspect the current implementation;
3. identify the smallest coherent change;
4. preserve architectural boundaries;
5. implement;
6. add/update tests;
7. create/update Alembic migration if schema changes;
8. run relevant checks;
9. review the diff;
10. report important decisions and limitations.

Do not modify unrelated code without a reason.

---

# 60. Definition of done

A task is complete when, where applicable:

* requested behavior is implemented;
* architecture boundaries remain intact;
* API contracts remain explicit;
* database changes have migrations;
* tests cover the behavior;
* relevant tests pass;
* lint/format checks pass;
* no secrets are introduced;
* documentation is updated;
* future features were not implemented unnecessarily.

When finishing a task report:

```text
Implemented
Database/migrations
Tests executed
Important decisions
Deferred intentionally
Remaining issues
```

Never report an unexecuted check as successful.

# 61. Canonical JSON + IFC import workflow

Administrative catalogue ingestion is a supported backend capability.

Use these working folders for source bundles:

```text
data/import/generic_solutions/
data/import/manufacturer_solutions/
```

Machine contracts are:

```text
schemas/import/generic_solutions.schema.json
schemas/import/manufacturer_solutions.schema.json
```

Rules:

- asset `uri` values are relative to the JSON file and must never escape its directory;
- every imported solution references at least one IFC in the current import contract;
- IFC files must be opened successfully with IfcOpenShell before persistence;
- source files are copied into managed `STORAGE_ROOT` with generated physical names;
- PostgreSQL stores only asset metadata, managed relative path, SHA-256 and validation/extraction data;
- functional asset IDs from JSON map to `Asset.code`; PostgreSQL UUIDs remain generated identities;
- generic imports upsert taxonomy/GenericSolution by functional code and replace that solution's Slots;
- manufacturer imports reference an existing GenericSolution by `generic_solution_code`;
- manufacturer imports may only create/update `DRAFT` CommercialSolutions and must never bypass submission/approval;
- a CommercialSolution code already owned by another Manufacturer must never be reassigned by import;
- imports must be transactional and idempotent for the same functional codes;
- do not put import persistence logic directly in CLI scripts; use the import Application Services.
