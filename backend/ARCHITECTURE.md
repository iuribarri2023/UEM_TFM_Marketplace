# AVRA VIVA Marketplace — Backend Architecture

## 1. Purpose

AVRA VIVA Marketplace is a web platform for consulting, managing and publishing construction solutions associated with BIM/IFC models.

This repository contains the backend only.

A separate web frontend will be implemented later and will communicate with this backend through a versioned REST API.

The backend architecture must:

* expose a stable API boundary;
* remain independent from the future frontend;
* separate business logic from HTTP;
* separate persistence from application use cases;
* support heterogeneous construction-product data;
* remain testable;
* allow incremental growth from PoC to production;
* remain conceptually portable to Java + Spring Boot.

The objective is not maximum architectural sophistication.

The objective is a clean and extensible system.

---

# 2. Architectural style

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

Microservices are intentionally avoided during the initial stages.

All backend modules are deployed together while maintaining explicit internal boundaries.

---

# 3. System context

```text
                ┌─────────────────────┐
                │    Web Frontend     │
                │   future project    │
                └──────────┬──────────┘
                           │
                           │ HTTPS / JSON
                           │
                           ▼
                ┌─────────────────────┐
                │      REST API       │
                │       Flask         │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Application Services│
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │       Domain        │
                └──────────┬──────────┘
                           │
                  ┌────────┴─────────┐
                  │                  │
                  ▼                  ▼
          ┌──────────────┐   ┌──────────────┐
          │ Repositories │   │ FileStorage  │
          └───────┬──────┘   └───────┬──────┘
                  │                  │
                  ▼                  ▼
          ┌──────────────┐   ┌──────────────┐
          │ PostgreSQL   │   │ Filesystem   │
          └──────────────┘   └──────────────┘
```

The frontend never communicates directly with PostgreSQL or storage.

---

# 4. Dependency direction

Primary dependency direction:

```text
HTTP / API
    ↓
Application Services
    ↓
Domain
    ↓
Persistence abstractions
    ↓
Infrastructure
```

Typical request:

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

Framework details should remain near the outside of the architecture.

---

# 5. HTTP / API layer

Technology:

```text
Flask
Flask Blueprints
Pydantic
```

Responsibilities:

* routing;
* HTTP method handling;
* path/query parameter parsing;
* request validation;
* authentication context extraction;
* invoking Application Services;
* serialization;
* HTTP status codes;
* exception-to-HTTP mapping.

The API layer does not implement business workflows or persistence queries.

---

# 6. Application layer

Application Services implement use cases.

Examples:

```text
CatalogService
GenericSolutionService
AuthenticationService
CommercialSolutionService
ApprovalService
AssetService
CatalogImportService
BimService
```

Application Services coordinate:

* repositories;
* domain rules;
* transactions;
* authorization;
* storage;
* BIM processing;
* auditing.

They must not depend on Flask.

---

# 7. Domain layer

The domain expresses business concepts and rules.

Initial important concepts:

```text
System
Subsystem
Archetype
GenericSolution
GenericSolutionSlot
```

Future concepts:

```text
Manufacturer
User
CommercialSolution
Asset
Approval workflow
```

The domain must not return HTTP responses.

Semantic application/domain errors are mapped to HTTP by the API layer.

---

# 8. Persistence architecture

Persistence uses:

```text
PostgreSQL
SQLAlchemy 2.x
Alembic
psycopg
```

SQLAlchemy is used directly.

Flask-SQLAlchemy is not the architectural core.

Flow:

```text
Application Service
       ↓
Repository
       ↓
SQLAlchemy
       ↓
PostgreSQL
```

Repositories isolate persistence queries from use cases.

---

# 9. Transactions

Transactions are explicit.

Normal success flow:

```text
Request
   ↓
Session
   ↓
Application Service
   ↓
Repositories
   ↓
commit
   ↓
close
```

Failure flow:

```text
Request
   ↓
Session
   ↓
Application Service
   ↓
Exception
   ↓
rollback
   ↓
close
```

Repositories should not independently commit.

One application use case normally corresponds to one transaction boundary.

---

# 10. Catalogue taxonomy

The initial AVRA catalogue hierarchy is:

```text
System
    ↓
Subsystem
    ↓
Archetype
    ↓
GenericSolution
```

Example:

```text
Envolvente
    ↓
Fachadas
    ↓
Fachada ventilada
    ↓
FAC-VEN-001
```

This hierarchy is relational because:

* entities have identity;
* relationships are stable;
* hierarchy is frequently queried;
* foreign-key integrity is valuable.

---

# 11. Extended GenericSolution composition

GenericSolution now also contains first-class Slots.

Full initial hierarchy:

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

Relationally:

```text
System
  |
  +-- Subsystem
        |
        +-- Archetype
              |
              +-- GenericSolution
                      |
                      +-- GenericSolutionSlot
                      +-- GenericSolutionSlot
                      +-- GenericSolutionSlot
```

A GenericSolution can have zero or many Slots.

Slots are composition children of GenericSolution.

---

# 12. Why Slots are relational

Slots have stable structural semantics across different product categories.

A Slot consistently has concepts such as:

```text
identity
parent solution
key
name
role
sequence
required/optional state
```

These characteristics justify relational persistence.

However, the technical contents inside a Slot vary substantially.

Therefore the architecture combines:

```text
Relational Slot envelope
+
JSONB technical content
```

---

# 13. Why Slots must remain generic

Different construction products use Slots differently.

Facade example:

```text
Revestimiento exterior
Cámara de aire
Aislamiento
Hoja principal
Revestimiento interior
```

Roof example:

```text
Protección
Capa separadora
Impermeabilización
Aislamiento
Formación de pendientes
Soporte resistente
```

Window example:

```text
Marco
Acristalamiento
```

The database must not encode one topology as the universal model.

A Slot can represent:

* a physical layer;
* a component;
* a subassembly;
* a functional position;
* a replaceable technical component;
* a subsystem.

---

# 14. Product-family independence

The same model must support future construction products.

Examples:

```text
doors
partitions
floors
structural systems
HVAC
heat pumps
ventilation systems
photovoltaic systems
other construction products
```

The architecture must not require:

```text
FacadeSolution
RoofSolution
WindowSolution
```

nor:

```text
FacadeSlot
RoofSlot
WindowSlot
```

as separate persistence models.

Product-specific behavior may later exist at the application/domain validation layer without requiring separate physical database schemas.

---

# 15. Hybrid relational + JSONB strategy

The database intentionally combines relational modelling with JSONB.

Use relational structures when the information has:

* stable identity;
* stable relationships;
* ordering;
* lifecycle;
* referential integrity requirements;
* important query semantics.

Use JSONB where structures genuinely vary between product categories.

This prevents two extremes:

```text
Everything relational
```

which would produce many nullable/product-specific tables,

and:

```text
Everything JSONB
```

which would lose relational integrity and make core queries harder.

---

# 16. Initial relational entities

Initial SQL entities are:

```text
System
Subsystem
Archetype
GenericSolution
GenericSolutionSlot
```

Future SQL entities include:

```text
Manufacturer
User
CommercialSolution
Asset
AuditLog
```

---

# 17. System model

Conceptual table:

```text
systems
-------

id UUID PK
code VARCHAR UNIQUE NOT NULL
name_es VARCHAR NOT NULL
description TEXT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

UUID is the database identity.

AVRA `code` is a functional identifier.

---

# 18. Subsystem model

```text
subsystems
----------

id UUID PK
system_id UUID FK NOT NULL
code VARCHAR UNIQUE NOT NULL
name_es VARCHAR NOT NULL
description TEXT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Relationship:

```text
System 1 ─── N Subsystem
```

---

# 19. Archetype model

```text
archetypes
----------

id UUID PK
subsystem_id UUID FK NOT NULL
code VARCHAR UNIQUE NOT NULL
name_es VARCHAR NOT NULL
description TEXT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Relationship:

```text
Subsystem 1 ─── N Archetype
```

---

# 20. GenericSolution model

Conceptual table:

```text
generic_solutions
-----------------

id UUID PK

archetype_id UUID FK NOT NULL

code VARCHAR UNIQUE NOT NULL

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

Relationship:

```text
Archetype 1 ─── N GenericSolution
```

---

# 21. Why GenericSolution no longer has only technical_data

An earlier simplified architecture considered:

```text
technical_data JSONB
```

as a single variable technical-data container.

The current canonical AVRA representation has evolved into clearer semantic blocks.

Therefore the preferred persistence model separates:

```text
attributes
metrics
classifications
source_references
cte_compliance
environmental_data
economic_data
industrialization_data
viva_metrics
data_quality_notes
```

while keeping each internally flexible through JSONB.

This improves clarity without over-normalizing product-specific structures.

---

# 22. GenericSolution attributes

`attributes JSONB` stores properties describing the solution itself.

Examples vary by category.

Facade-like concepts may include:

```text
is_external
load_bearing
total_thickness
```

Roof-like concepts may include:

```text
is_thermal_envelope
roof_type
ventilation
trafficability
vegetated
```

Window-like concepts may include:

```text
width_mm
height_mm
opening_area_m2
opening_type
frame_material
glazing_type
ifc_entity
```

These differences justify JSONB rather than dozens of nullable SQL columns.

---

# 23. GenericSolution metrics

`metrics JSONB` stores performance metrics associated with the complete solution.

Examples may include:

```text
U-value
surface mass
waterproofing performance
fire resistance
acoustic performance
slope
whole-window thermal performance
solar factor
```

Metrics may contain nested:

```text
value
unit
range
status
source
calculation
assumptions
```

The database should preserve those structures.

---

# 24. GenericSolution classifications

`classifications JSONB` stores zero or more classification references.

Different systems may include:

```text
CTE-CEC
IVE-BDC
IFC
future AVRA/external classification systems
```

Classification normalization can be reconsidered later if cross-catalogue classification queries become a significant requirement.

---

# 25. GenericSolution source references

`source_references JSONB` preserves technical/economic/reference provenance associated with the whole solution.

Source structures may vary by dataset.

Do not force them into one rigid SQL schema during the initial PoC.

---

# 26. CTE compliance

`cte_compliance JSONB` contains regulatory evaluation and related information.

Its shape may vary according to:

* construction-product category;
* applicable regulation;
* metric being evaluated.

Therefore it remains JSONB initially.

---

# 27. Environmental data

`environmental_data JSONB` preserves environmental information.

It may contain:

```text
GWP values
units
modules
aggregation
observations
components
sources
statuses
```

Do not reduce this model to a single fixed `gwp` SQL column.

---

# 28. Economic data

`economic_data JSONB` preserves the complete economic representation.

Possible contents include:

```text
functional_unit
currency
unit_cost
scope
source
BC3 decomposition
source observations
status
notes
```

Do not normalize BC3 decomposition during the first persistence iteration.

This may become relational later if independent analytics/querying over BC3 items becomes important.

---

# 29. Industrialization data

Keep:

```text
industrialization_data JSONB
viva_metrics JSONB
```

These structures are semantically meaningful but still evolving.

They should not be prematurely normalized.

---

# 30. GenericSolutionSlot model

Conceptual table:

```text
generic_solution_slots
----------------------

id UUID PK

generic_solution_id UUID FK NOT NULL

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

Relationship:

```text
GenericSolution 1 ─── N GenericSolutionSlot
```

Slots should normally be deleted when their parent GenericSolution is deleted.

Therefore:

```text
ON DELETE CASCADE
```

is appropriate for the relational FK.

---

# 31. Slot identity

Slot identity is:

```text
GenericSolutionSlot.id
```

using UUID.

`key` is not database identity.

For example:

```text
AT
FRM
GLZ
HP
RE
I
SR
```

are semantic keys.

The same key may appear:

* across many GenericSolutions;
* more than once inside one GenericSolution.

Therefore:

```text
UNIQUE(generic_solution_id, key)
```

must NOT be assumed.

---

# 32. Slot sequence

`sequence` determines intended ordering.

Example:

```text
10
20
30
40
...
```

Indexes should support retrieving:

```text
Slots for solution ordered by sequence
```

Suggested index:

```text
(generic_solution_id, sequence)
```

Sequence need not automatically be unique.

---

# 33. Slot properties

`properties JSONB` contains variable technical information.

Facade example:

```json
{
  "material_family": "mineral_wool",
  "product_family": "mineral_wool_board",
  "thickness": 100
}
```

Roof example:

```json
{
  "material_family": "bituminous_membrane",
  "system": "monocapa",
  "installation": "no_adherida"
}
```

Window example:

```json
{
  "type": "double",
  "panes": 2,
  "outer_pane_mm": 4,
  "cavity_1_mm": 12,
  "inner_pane_mm": 4
}
```

All three belong to the same SQL column:

```text
properties JSONB
```

---

# 34. Slot metrics

Slots can optionally contain component-specific performance.

This is particularly important for products such as windows.

Example:

```text
Frame Slot
    └── Uf

Glazing Slot
    ├── Ug
    ├── solar factor
    └── light transmittance
```

Use:

```text
metrics JSONB NULL
```

This must remain separate from solution-level metrics.

---

# 35. Slot source reference

Some Slots may have dedicated source/provenance information.

Use:

```text
source_reference JSONB NULL
```

This differs from the solution-level collection:

```text
source_references JSONB
```

---

# 36. Why Slot properties are not EAV

An alternative would be:

```text
Slot
   ↓
SlotAttribute
   ↓
key / type / unit / value
```

This architecture is intentionally not selected initially.

Reasons:

* the canonical JSON already represents properties naturally as objects;
* nested structures are possible;
* arrays may occur;
* technical properties vary by category;
* EAV increases query and validation complexity;
* it provides little benefit for the current PoC.

A property-definition/form-schema system may be added later if dynamic forms require it.

---

# 37. Example resulting persistence structure

Conceptually:

```text
systems
└── ENV

subsystems
└── FAC
└── ROF
└── WIN

archetypes
├── FAC-VEN
├── ROF-PLN
└── WIN-ALU

generic_solutions
├── FAC-VEN-001
├── ROF-PLN-001
└── WIN-ALU-001
```

Their Slot structures can differ completely:

```text
FAC-VEN-001
├── RE
├── C
├── AT
├── HP
└── RI

ROF-PLN-001
├── P
├── Csa
├── I
├── AT
├── FP
└── SR

WIN-ALU-001
├── FRM
└── GLZ
```

No database migration is required merely because these solution categories have different Slot structures.

---

# 38. Canonical JSON versus database model

The canonical JSON is an interchange/import/export representation.

PostgreSQL is the operational persistence model.

They should map clearly but do not need to be structurally identical.

Conceptual mapping:

```text
system
    -> systems row

subsystem
    -> subsystems row

archetype
    -> archetypes row

generic_solutions[]
    -> generic_solutions rows

generic_solutions[].slots[]
    -> generic_solution_slots rows
```

Nested technical blocks are stored using JSONB.

---

# 39. Top-level JSON metadata

Canonical documents may contain:

```text
schema_version
data_template
property_dictionary
regulatory_profile
normalization_profile
industrialization_profile
generation_provenance
```

These fields describe the source/import document rather than necessarily a single GenericSolution business entity.

Do not duplicate all top-level import metadata into every solution row.

A future importer may introduce:

```text
ImportBatch
ImportRun
CatalogSource
```

if source-version tracking becomes necessary.

This is intentionally deferred.

---

# 40. Null and unresolved values

Canonical technical data can intentionally contain null.

Example conceptually:

```json
{
  "value": null,
  "status": "not_available_from_mapped_sources"
}
```

This means "unknown/unavailable", not zero.

The persistence layer must preserve this distinction.

Do not automatically:

* replace null with zero;
* remove explanatory status;
* infer values from similar solutions.

---

# 41. DTO architecture

Pydantic defines API/application contracts.

Conceptually:

```text
JSON request
     ↓
Pydantic DTO
     ↓
Application Service
     ↓
Domain / Repository
```

SQLAlchemy persistence models are separate from Pydantic DTOs.

A GenericSolution response may conceptually expose:

```text
id
code
name_es
description
functional_unit
classifications
source_references
attributes
metrics
cte_compliance
environmental_data
economic_data
industrialization_data
viva_metrics
slots
```

A Slot DTO may expose:

```text
id
key
name_es
role
sequence
required
properties
metrics
source_reference
```

---

# 42. API boundary with the frontend

The future frontend consumes:

```text
/api/v1
```

The frontend does not depend on:

* SQLAlchemy models;
* SQL table names;
* PostgreSQL JSONB implementation details;
* Python exceptions;
* filesystem paths.

The REST API is the integration contract.

---

# 43. API response structure

Success:

```json
{
  "data": {
    "id": "...",
    "name_es": "..."
  }
}
```

Error:

```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "The requested entity does not exist."
  }
}
```

Internal implementation details must not leak to API consumers.

---

# 44. API versioning

Marketplace endpoints use:

```text
/api/v1
```

Operational endpoints such as:

```text
GET /health
```

can remain outside the versioned business API.

---

# 45. OpenAPI

Because frontend and backend are independent applications, the API should have an explicit contract.

Initially this may be represented by:

```text
openapi.yaml
```

The architecture must not couple domain/application logic to a particular documentation framework.

---

# 46. CORS

The frontend may run on another origin.

Allowed origins are configured through:

```text
CORS_ORIGINS
```

Do not hardcode frontend development URLs in business/application code.

---

# 47. Future GenericSolution assets

GenericSolution will eventually reference Assets.

Conceptual model:

```text
GenericSolution
      |
      +-- Asset
      +-- Asset
```

Files themselves do not live in PostgreSQL.

Assets are intentionally not embedded permanently in GenericSolution JSONB because they will have identity, file metadata and lifecycle.

---

# 48. Future file architecture

Physical files live behind:

```text
FileStorage
```

Initial implementation:

```text
LocalFileStorage
```

Possible future adapters:

```text
S3FileStorage
AzureBlobStorage
MinIOFileStorage
```

PostgreSQL stores metadata and relative paths.

Do not store IFC/PDF/images as BLOB/BYTEA.

---

# 49. Future BIM architecture

IfcOpenShell is isolated behind an adapter.

```text
Application Service
       ↓
BimService
       ↓
IfcOpenShellAdapter
```

The backend will eventually provide:

* validation;
* metadata extraction;
* access control;
* file delivery.

3D visualization belongs to the frontend.

---

# 50. Future commercial marketplace

Commercial products will eventually follow:

```text
GenericSolution
       ↑
       |
CommercialSolution
       |
       ↓
Manufacturer
```

The GenericSolution/Slot structure provides the generic reference model.

Commercial products can later reference or implement compatible components without redesigning the generic catalogue.

The exact CommercialSolution/Slot relationship should be implemented only when its functional requirements are defined.

---

# 51. Future workflow

CommercialSolution will later introduce states such as:

```text
DRAFT
   ↓
SUBMITTED
   ↓
APPROVED / REJECTED
```

This workflow is outside the initial GenericSolution persistence foundation.

---

# 52. Configuration

Expected environment variables include:

```text
APP_ENV
DATABASE_URL
JWT_SECRET_KEY
STORAGE_ROOT
MAX_UPLOAD_SIZE
CORS_ORIGINS
```

Supported environments:

```text
development
testing
production
```

Secrets are never committed.

---

# 53. Application Factory

Flask uses:

```python
create_app()
```

Conceptually:

```python
def create_app(config=None):
    app = Flask(__name__)

    configure_app(app)
    configure_database(app)

    register_blueprints(app)
    register_error_handlers(app)

    return app
```

The application must not be concentrated into one giant `app.py`.

---

# 54. Backend package structure

Target:

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
├── docs/
├── storage/
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

Structure is responsibility-driven.

Empty packages do not need to be created unnecessarily.

---

# 55. Initial database indexes

Initial useful indexes include:

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

Do not add JSONB GIN indexes before concrete query requirements exist.

---

# 56. Testing architecture

```text
tests/unit
tests/integration
tests/api
```

Unit tests:

* Services;
* domain rules;
* workflow;
* permission behavior.

Integration tests:

* repositories;
* PostgreSQL;
* JSONB persistence;
* FileStorage later;
* BIM adapters later.

API tests:

* Flask routes;
* request validation;
* response serialization;
* status codes;
* authentication later.

---

# 57. Catalogue persistence tests

The GenericSolution model must be verified against heterogeneous examples.

At minimum representative tests should demonstrate persistence for:

```text
Facade-like GenericSolution
Roof-like GenericSolution
Window-like GenericSolution
```

Tests should prove:

* solution-level JSONB structures vary safely;
* Slot property structures vary safely;
* Slots can have metrics or no metrics;
* duplicate Slot keys are valid;
* Slots retain ordering;
* new technical properties do not require new SQL columns.

PostgreSQL integration tests should be used for PostgreSQL-specific behavior.

---

# 58. Local development

Docker Compose should provide PostgreSQL.

Conceptually:

```text
docker-compose
├── backend
└── postgres
```

PostgreSQL uses persistent storage.

The backend should also be runnable locally outside Docker when convenient.

---

# 59. Initial production topology

```text
Internet
   |
   v
 Nginx
   |
   v
Gunicorn
   |
   v
 Flask
   |
   +------ PostgreSQL
   |
   +------ persistent FileStorage
```

No distributed infrastructure is required initially.

---

# 60. Future Spring Boot equivalence

Conceptual mapping:

```text
Python                         Java

Flask Blueprint               @RestController
Pydantic DTO                  DTO / Java Record
Application Service           @Service
Repository                    Repository
SQLAlchemy                    JPA / Hibernate
Alembic                       Flyway / Liquibase
JWT authentication            Spring Security
FileStorage                   StorageService
BimService                    BIM adapter/service
```

The objective is portability of boundaries and responsibilities.

---

# 61. Explicitly avoided initial architecture

Do not initially implement:

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
complex distributed processing
advanced versioning
workflow engine
one table per construction-product family
one table per archetype
one table per Slot type
EAV technical-property system
BLOB storage for IFC
```

---

# 62. Development roadmap

Current roadmap:

```text
Phase 1
Backend skeleton
+
Generic catalogue persistence foundation
+
GenericSolutionSlot persistence

Phase 2
Generic catalogue REST API

Phase 3
Canonical JSON catalogue importer

Phase 4
Manufacturers + authentication

Phase 5
Commercial solutions

Phase 6
Assets + FileStorage

Phase 7
BIM

Phase 8
Approval workflow
```

Each phase should leave the system executable and tested.

---

# 63. Architectural principles

The implementation follows:

```text
Separation of Concerns
Dependency Inversion
Repository Pattern
Application Service Layer
DTO separation
Explicit transactions
Framework-independent business logic
Hybrid relational + JSONB modelling
```

Without unnecessary academic complexity.

The main architectural rules are:

```text
Flask manages HTTP.

Pydantic manages data contracts.

Application Services manage use cases.

Domain manages business rules.

Repositories abstract persistence.

SQLAlchemy communicates with PostgreSQL.

GenericSolutionSlot models structural solution components.

JSONB stores genuinely variable technical structures.

FileStorage manages files.

BimService manages IFC.
```

This separation must remain the governing principle as AVRA VIVA grows.

# 64. Canonical import boundary

The backend has an administrative file-ingestion boundary for reproducible catalogue loading:

```text
JSON bundle + referenced IFC files
        ↓
Pydantic import contract / JSON Schema
        ↓
CatalogImportService or ManufacturerSolutionImportService
        ↓
Repositories + FileStorage + BimService
        ↓
PostgreSQL + managed filesystem storage
```

Source bundles live under `data/import/generic_solutions/` or `data/import/manufacturer_solutions/`. Asset paths in source JSON are relative bundle paths; they are never persisted as physical storage paths. Import services stage files, validate IFC with IfcOpenShell, calculate SHA-256, promote files into managed `STORAGE_ROOT`, then persist Asset metadata and association-table links.

Generic imports map canonical `system/subsystem/archetype/generic_solutions/slots/assets` data into the relational + JSONB catalogue model. Manufacturer imports map organization data and `manufacturer_solutions` into Manufacturer + DRAFT CommercialSolution rows referencing an existing GenericSolution. Workflow states beyond DRAFT are not importable.
