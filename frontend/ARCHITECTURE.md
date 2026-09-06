# AVRA VIVA Marketplace Frontend — Architecture

## 1. Purpose

This document defines the frontend architecture for AVRA VIVA Marketplace against the current Flask backend implementation.

The design has four objectives:

1. stay exactly compatible with the backend REST contract;
2. use Angular for application-level concerns such as routing, authentication, forms, and workflow UI;
3. keep BIM/IFC visualization independent from Angular;
4. keep the first version simple enough for a TFM proof of concept while preserving clean extension points.

---

## 2. Technology baseline

Application shell:

```text
Angular 22.x
TypeScript 6.x as supported by the selected Angular 22 release
Angular Router
Angular HttpClient
Angular Signals
RxJS
SCSS
Vitest through Angular CLI
```

BIM viewer package:

```text
Plain TypeScript
That Open Company Components
That Open Company Components Front, only where browser-specific functionality is needed
That Open Fragments
Three.js
WebIFC as required by compatible That Open versions
```

Do not assume that all That Open packages can be upgraded independently. Use a mutually compatible version set and commit the lockfile.

---

## 3. System context

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  VIVA Angular SPA                         │  │
│  │                                                           │  │
│  │  Public Catalogue  Marketplace  Auth  Manufacturer Admin │  │
│  │                                   Workspace     Review     │  │
│  └───────────────┬─────────────────────────────┬─────────────┘  │
│                  │                             │                │
│                  │ REST/JSON + files           │ Uint8Array     │
│                  ▼                             ▼                │
│         ┌──────────────────┐          ┌─────────────────────┐   │
│         │ Angular API     │          │ VIVA IFC Viewer     │   │
│         │ adapters        │          │ plain TypeScript    │   │
│         └────────┬────────┘          └──────────┬──────────┘   │
└──────────────────┼──────────────────────────────┼───────────────┘
                   │                              │
                   ▼                              ▼
          ┌─────────────────┐            ┌────────────────────┐
          │ Flask REST API  │            │ That Open / Three │
          │ /api/v1         │            │ browser runtime    │
          └────────┬────────┘            └────────────────────┘
                   │
          ┌────────┴─────────┐
          ▼                  ▼
     PostgreSQL         File storage
                         + IfcOpenShell validation
```

The backend validates IFCs for business acceptance. The browser viewer visualizes them. These responsibilities are deliberately different.

---

## 4. Architectural boundaries

### 4.1 Angular application

Owns:

- routing;
- page composition;
- authentication/session UX;
- bearer-token HTTP integration;
- role guards;
- API orchestration;
- feature state;
- reactive forms;
- technical-data rendering;
- file upload/download orchestration;
- marketplace filtering;
- manufacturer workflow controls;
- administrator review UI;
- lifecycle of the Angular host component around the IFC viewer.

Does not own:

- backend authorization rules;
- persistence;
- IFC business validation;
- direct Three.js/That Open implementation scattered across features.

### 4.2 `viva-contracts`

A framework-neutral package containing transport types, enums/unions, and small pure helpers.

It must not import Angular.

Example exports:

```text
ApiEnvelope<T>
ApiErrorEnvelope
UserRole
CommercialSolutionStatus
SystemDto
SubsystemDto
ArchetypeDto
GenericSolutionDto
AssetDto
ManufacturerDto
CommercialSolutionDto
```

### 4.3 `viva-ifc-viewer`

A framework-neutral browser package.

Owns:

- creation/disposal of That Open component system;
- scene/camera/renderer lifecycle;
- Fragments worker setup;
- IFC loading from `Uint8Array`;
- model attach/remove;
- fit/reset view;
- selection/properties when added;
- visibility/isolation when added;
- clipping when added;
- release of GPU/worker/listener resources.

Does not own:

- REST URLs;
- `HttpClient`;
- tokens;
- VIVA permissions;
- VIVA workflow state;
- Angular components/services.

---

## 5. Proposed repository layout

```text
frontend/
├── AGENTS.md
├── ARCHITECTURE.md
├── README.md
├── package.json
├── package-lock.json
│
├── apps/
│   └── viva-web/
│       ├── angular.json
│       ├── proxy.conf.json
│       ├── tsconfig*.json
│       └── src/
│           ├── main.ts
│           ├── styles.scss
│           └── app/
│               ├── app.config.ts
│               ├── app.routes.ts
│               │
│               ├── core/
│               │   ├── api/
│               │   ├── auth/
│               │   ├── errors/
│               │   └── layout/
│               │
│               ├── shared/
│               │   ├── ui/
│               │   ├── technical-data/
│               │   └── assets/
│               │
│               └── features/
│                   ├── catalogue/
│                   ├── marketplace/
│                   ├── manufacturers/
│                   ├── manufacturer-workspace/
│                   ├── admin-review/
│                   └── bim/
│
└── packages/
    ├── viva-contracts/
    │   └── src/
    └── viva-ifc-viewer/
        └── src/
```

A simpler root layout is acceptable if the dependency boundaries remain identical.

---

## 6. Backend contract overview

### 6.1 Success envelope

```ts
interface ApiEnvelope<T> {
  data: T;
}
```

### 6.2 Error envelope

```ts
interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
  };
}
```

### 6.3 Roles

```ts
type UserRole = 'ADMIN' | 'MANUFACTURER';
```

### 6.4 Commercial states

```ts
type CommercialSolutionStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'ARCHIVED';
```

---

## 7. Backend endpoint matrix

| Area | Method | Route | Auth | Notes |
|---|---|---|---|---|
| Catalogue | GET | `/api/v1/systems` | public | all systems |
| Catalogue | GET | `/api/v1/systems/{id}` | public | UUID lookup |
| Catalogue | GET | `/api/v1/systems/by-code/{code}` | public | functional code lookup |
| Catalogue | GET | `/api/v1/subsystems` | public | optional `system_id` |
| Catalogue | GET | `/api/v1/subsystems/{id}` | public | UUID lookup |
| Catalogue | GET | `/api/v1/subsystems/by-code/{code}` | public | code lookup |
| Catalogue | GET | `/api/v1/archetypes` | public | optional `subsystem_id` |
| Catalogue | GET | `/api/v1/archetypes/{id}` | public | UUID lookup |
| Catalogue | GET | `/api/v1/archetypes/by-code/{code}` | public | code lookup |
| Catalogue | GET | `/api/v1/generic-solutions` | public | optional `archetype_id` |
| Catalogue | GET | `/api/v1/generic-solutions/{id}` | public | includes slots/assets |
| Catalogue | GET | `/api/v1/generic-solutions/by-code/{code}` | public | includes slots/assets |
| Marketplace | GET | `/api/v1/marketplace/commercial-solutions` | public | approved only; 5 filters |
| Marketplace | GET | `/api/v1/marketplace/commercial-solutions/{id}` | public | approved only |
| Marketplace | GET | `/api/v1/manufacturers` | public | active only |
| Marketplace | GET | `/api/v1/manufacturers/{id}` | public | active only |
| Auth | POST | `/api/v1/auth/login` | public | returns access + refresh |
| Auth | POST | `/api/v1/auth/refresh` | public | refresh token in JSON body |
| Auth | GET | `/api/v1/auth/me` | bearer | authoritative user |
| Manufacturer | GET | `/api/v1/manufacturer/commercial-solutions` | manufacturer | own solutions only |
| Manufacturer | POST | `/api/v1/manufacturer/commercial-solutions` | manufacturer | creates `DRAFT` |
| Manufacturer | GET | `/api/v1/manufacturer/commercial-solutions/{id}` | manufacturer | own only |
| Manufacturer | PATCH | `/api/v1/manufacturer/commercial-solutions/{id}` | manufacturer | constrained by workflow |
| Manufacturer | DELETE | `/api/v1/manufacturer/commercial-solutions/{id}` | manufacturer | draft/rejected only |
| Manufacturer | POST | `/api/v1/manufacturer/commercial-solutions/{id}/submit` | manufacturer | requires valid IFC |
| Assets | GET | `/api/v1/manufacturer/commercial-solutions/{id}/assets` | manufacturer | own only |
| Assets | POST | `/api/v1/manufacturer/commercial-solutions/{id}/assets` | manufacturer | draft/rejected only |
| Assets | DELETE | `/api/v1/manufacturer/commercial-solutions/{id}/assets/{asset_id}` | manufacturer | draft/rejected only |
| Assets | GET | `/api/v1/assets/{id}/download` | conditional | public or authorized |
| Admin | GET | `/api/v1/admin/commercial-solutions/submitted` | admin | complete submitted queue |
| Admin | POST | `/api/v1/admin/commercial-solutions/{id}/approve` | admin | submitted only |
| Admin | POST | `/api/v1/admin/commercial-solutions/{id}/reject` | admin | submitted only; reason required |

No frontend code may call an endpoint absent from this matrix without an intentional backend change.

---

## 8. Transport types

### 8.1 Catalogue

```ts
export interface SystemDto {
  id: string;
  code: string;
  name_es: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubsystemDto {
  id: string;
  system_id: string;
  code: string;
  name_es: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArchetypeDto {
  id: string;
  subsystem_id: string;
  code: string;
  name_es: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}
```

`GenericSolutionSummaryDto` contains:

```text
id
archetype_id
code
name_es
description
functional_unit
status
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
created_at
updated_at
```

`GenericSolutionDto` adds:

```text
slots: GenericSolutionSlotDto[]
assets: AssetDto[]
```

### 8.2 Asset

```ts
export interface AssetDto {
  id: string;
  code: string | null;
  original_filename: string;
  mime_type: string;
  size: number;
  sha256: string;
  asset_type: string;
  format: string;
  role: string;
  uploaded_by: string | null;
  validation_data: Record<string, unknown> | null;
  extraction_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}
```

### 8.3 Manufacturer

```ts
export interface ManufacturerDto {
  id: string;
  code: string;
  name: string;
  tax_id: string | null;
  website: string | null;
  description: string | null;
  status: string;
}
```

### 8.4 Commercial solution

```ts
export interface CommercialSolutionDto {
  id: string;
  manufacturer_id: string;
  generic_solution_id: string;
  code: string;
  name_es: string;
  description: string | null;
  technical_data: Record<string, unknown>;
  status: CommercialSolutionStatus;
  rejection_reason: string | null;
  created_by: string | null;
  updated_by: string | null;
  submitted_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
  created_at: string;
  updated_at: string;
  assets: AssetDto[];
}
```

Create and patch DTOs are deliberately narrower than read DTOs.

---

## 9. Application routes

Recommended first-version Angular routes:

```text
/                                  -> redirect to /catalogue
/catalogue                         -> taxonomy browser + generic solutions
/generic-solutions/:code           -> generic solution detail
/marketplace                       -> approved commercial solution listing
/marketplace/:id                   -> approved commercial solution detail
/manufacturers                     -> active manufacturer list
/manufacturers/:id                 -> manufacturer detail + filtered public products
/login                             -> login
/manufacturer/solutions            -> own solution list
/manufacturer/solutions/new        -> create solution
/manufacturer/solutions/:id/edit   -> edit/assets/submit
/admin/review                      -> submitted queue master/detail
/**                                -> not found
```

Lazy-load manufacturer/admin feature route trees.

Do not create `/admin/review/:id` as a hard requirement until a direct admin detail endpoint exists. If such a route is added purely client-side, it must be able to reconstruct its data from the submitted queue and handle an item that is no longer submitted.

---

## 10. Public catalogue design

### 10.1 Catalogue store

Maintain normalized maps where useful:

```text
systemsById
subsystemsById
archetypesById
genericSolutionsById
```

The catalogue page should support cascading selection:

```text
System → Subsystem → Archetype → GenericSolution
```

Queries map directly to backend filters:

```text
/subsystems?system_id=...
/archetypes?subsystem_id=...
/generic-solutions?archetype_id=...
```

Use the `by-code` generic detail endpoint for the public generic URL so functional AVRA codes remain visible/bookmarkable.

### 10.2 Generic detail

Render:

- identity and description;
- taxonomy context;
- functional unit/status;
- generic slots ordered by `sequence`;
- heterogeneous data sections;
- source references/classifications;
- assets;
- IFC viewer for available IFC assets;
- link/filter to approved commercial solutions for the same `generic_solution_id`.

The backend generic detail already includes assets. Do not invent another generic-asset listing endpoint.

---

## 11. Marketplace design

The backend returns commercial solutions with foreign-key IDs but does not embed manufacturer/generic summaries.

The frontend therefore resolves display names from existing public resources:

```text
/manufacturers
/generic-solutions
/archetypes
/subsystems
/systems
```

Maintain lookup maps rather than performing one HTTP request per card.

Marketplace filters must use the backend's supported query keys exactly:

```text
system_id
subsystem_id
archetype_id
generic_solution_id
manufacturer_id
```

Reflect active filters into Angular query parameters so marketplace URLs can be copied/bookmarked.

Commercial detail loads:

1. `/marketplace/commercial-solutions/{id}`;
2. manufacturer detail by `manufacturer_id`;
3. generic solution detail by `generic_solution_id`.

The commercial response includes assets. IFC assets are viewable because the solution is approved and the download endpoint is public for those assets.

---

## 12. Authentication architecture

### 12.1 AuthStore

Suggested state:

```ts
interface AuthState {
  user: CurrentUserDto | null;
  status: 'unknown' | 'anonymous' | 'authenticated';
  loading: boolean;
}
```

Token persistence is kept behind an `AuthTokenStore`.

Current backend requires JavaScript to send the refresh token in JSON. For v1, use `sessionStorage` for both tokens.

### 12.2 Startup

```text
App starts
  ↓
Token pair present?
  ├─ no → anonymous
  └─ yes
       ↓
     GET /auth/me
       ├─ success → authenticated user
       └─ 401 → one refresh attempt
                  ├─ success → retry /me
                  └─ failure → clear tokens → anonymous
```

### 12.3 Interceptor

A functional auth interceptor should:

- add `Authorization: Bearer ...` when an access token is available;
- skip refresh recursion for login/refresh calls;
- coalesce concurrent refresh attempts;
- retry a failed request once;
- clear invalid auth state when refresh fails.

Do not infer authorization solely from JWT payload decoding.

---

## 13. Manufacturer workspace

### 13.1 List

`GET /manufacturer/commercial-solutions` returns the authenticated manufacturer's own solutions.

Show:

- code/name;
- generic solution display name resolved from catalogue lookups;
- status badge;
- last update;
- rejection reason when present;
- valid IFC indicator;
- available workflow actions.

### 13.2 Create

POST payload is exactly:

```json
{
  "generic_solution_id": "uuid",
  "code": "...",
  "name_es": "...",
  "description": "...",
  "technical_data": {}
}
```

Do not send `manufacturer_id` even if the current user has one. Ownership comes from the JWT-backed user record.

The initial editor should include:

- generic solution selector;
- code;
- Spanish name;
- description;
- `technical_data` JSON-object editor with syntax/type validation.

After creation, navigate to the edit screen where assets can be uploaded.

### 13.3 Edit

PATCH may update only:

```text
code
name_es
description
technical_data
```

The current backend does not allow changing `generic_solution_id`. Show classification as read-only on edit.

For reliable asset state, call the dedicated asset-list endpoint in the edit screen.

### 13.4 Workflow action computation

Represent this as pure code, for example:

```ts
interface CommercialActions {
  canEdit: boolean;
  canChangeAssets: boolean;
  canSubmit: boolean;
  canDelete: boolean;
}
```

Derive from status and known assets for UX only.

Backend remains authoritative.

### 13.5 Submit

Before submit, the UI may check for an IFC asset with `validation_data.valid === true` and give immediate guidance.

Still call the backend and handle `MISSING_IFC_FILE`, because backend validation is authoritative.

---

## 14. Asset upload and download

### 14.1 Upload

Use `FormData`:

```ts
const formData = new FormData();
formData.append('file', file);
formData.append('role', role);
formData.append('asset_type', assetType);
if (code) formData.append('code', code);
```

Do not manually set the multipart `Content-Type` header; let the browser set the boundary.

Recommended defaults matching backend route defaults:

```text
role = primary_commercial_model
asset_type = bim_model
```

Allowed extension hints may include:

```text
.ifc,.pdf,.png,.jpg,.jpeg,.webp
```

Do not treat browser-side extension checking as authoritative.

### 14.2 Download

For normal download:

```text
GET /api/v1/assets/{id}/download
responseType: blob
```

For IFC visualization:

```text
GET /api/v1/assets/{id}/download
responseType: arraybuffer
        ↓
new Uint8Array(buffer)
        ↓
VivaIfcViewer.load(...)
```

The normal auth interceptor must add a bearer token when present so manufacturers/admins can view private assets they are authorized to access.

---

## 15. IFC viewer architecture

### 15.1 Public API

The Angular application should depend on an application-owned abstraction rather than That Open classes directly.

Suggested API:

```ts
export interface VivaIfcModelInput {
  id: string;
  name: string;
  bytes: Uint8Array;
}

export interface VivaIfcViewerEvents {
  loading?: (progress: number | null) => void;
  loaded?: (modelId: string) => void;
  error?: (error: unknown) => void;
  selectionChanged?: (selection: unknown) => void;
}

export class VivaIfcViewer {
  constructor(events?: VivaIfcViewerEvents);

  initialize(container: HTMLElement): Promise<void>;
  load(model: VivaIfcModelInput): Promise<void>;
  clear(): Promise<void>;
  fitToModel(): Promise<void> | void;
  dispose(): Promise<void> | void;
}
```

The implementation may evolve without changing Angular pages.

### 15.2 That Open setup

Use the current official That Open architecture:

```text
OBC.Components
OBC.Worlds
scene
renderer
camera
OBC.FragmentsManager
OBC.IfcLoader
```

Current That Open `IfcLoader` accepts IFC data as `Uint8Array` and produces/loads Fragments. Initialize the Fragments worker before loading IFCs.

Because the That Open APIs evolve, implementation code must be checked against the installed package versions and official examples. Do not paste obsolete pre-Fragments tutorials or rely on old `openbim-components` APIs.

### 15.3 Angular host

The host component is responsible for:

```text
ViewChild container
  ↓
viewer.initialize(container)
  ↓
AssetApi.downloadArrayBuffer(asset.id)
  ↓
viewer.load({ id, name, bytes })
```

On destroy:

```text
viewer.dispose()
```

Use dynamic import/lazy route/component loading so That Open packages are not part of the initial marketplace bundle when avoidable.

### 15.4 First viewer milestone

Required:

- initialize scene;
- load one IFC asset from backend bytes;
- orbit/pan/zoom through That Open camera controls;
- fit model;
- clear/change model;
- loading/error state;
- full cleanup.

Preferred if straightforward with current APIs:

- element selection/highlight;
- basic property display;
- hide/isolate/show-all;
- clipping plane.

Not required for first milestone:

- BCF;
- clash detection;
- model federation;
- measurement suite;
- 2D drawing generation;
- IFC editing/export.

---

## 16. Generic technical-data rendering

The backend intentionally stores heterogeneous JSONB data.

Create reusable recursive rendering primitives rather than hard-coded product-family templates.

Recommended concepts:

```text
TechnicalSection
JsonObjectTable
JsonArrayList
MetricValue
SourceReferenceCard
DataQualityBadge
GenericSlotList
```

Rendering strategy:

```text
null              -> em dash / unavailable
string/number     -> scalar value
boolean           -> yes/no indicator
array of scalars  -> chips/list
array of objects  -> repeated cards/table
object            -> nested labeled key/value grid
```

Special-case presentation only when the object shape is confidently recognized, for example a metric object containing `value` and `unit`. Keep a generic fallback.

Do not drop unknown keys from backend JSON.

---

## 17. Administrator review

The current admin API exposes only the submitted queue and approve/reject actions.

Recommended `/admin/review` layout:

```text
┌─────────────────────┬────────────────────────────────────┐
│ Submitted queue     │ Selected solution                  │
│                     │                                    │
│ SOL-001             │ identity / technical data          │
│ SOL-002             │ assets / IFC viewer                │
│ SOL-003             │ metadata                            │
│                     │                                    │
│                     │ [Reject] [Approve]                 │
└─────────────────────┴────────────────────────────────────┘
```

Reject requires:

```json
{
  "reason": "non-empty string up to 2000 chars"
}
```

After approve or reject, reload or remove the item from the submitted queue.

If an action returns `INVALID_WORKFLOW_TRANSITION`, refresh the queue because another actor may already have reviewed the item.

Manufacturer names can be resolved from `/manufacturers` when active; if an admin item references a manufacturer not present in the public active-manufacturer list, fall back to displaying its UUID because no admin manufacturer lookup endpoint currently exists.

---

## 18. Error architecture

Normalize `HttpErrorResponse` into an application representation when the body matches the backend envelope:

```ts
interface AppApiError {
  status: number;
  code: string;
  message: string;
}
```

Important mappings:

| Code | Typical HTTP | Frontend reaction |
|---|---:|---|
| `AUTHENTICATION_FAILED` | 401 | refresh or login feedback |
| `PERMISSION_DENIED` | 403 | forbidden state |
| `ENTITY_NOT_FOUND` | 404 | entity not found |
| `NOT_FOUND` | 404 | invalid API route/not-found |
| `VALIDATION_FAILED` | 400 | field/action feedback |
| `INVALID_IFC_FILE` | 400 | upload validation feedback |
| `INTEGRITY_ERROR` | 409 | conflict/duplicate feedback |
| `INVALID_WORKFLOW_TRANSITION` | 409 | refresh stale entity/queue |
| `MISSING_IFC_FILE` | 409 | require backend-valid IFC |
| `FILE_TOO_LARGE` | 413 | upload size feedback |
| `STORAGE_ERROR` | 400 | asset operation feedback |
| `INTERNAL_SERVER_ERROR` | 500 | generic failure + retry path |

Do not base critical branching on human-readable `message` strings.

---

## 19. State management

Use feature-local stores/facades based on Signals.

Example:

```text
AuthStore
  user
  authStatus
  loginLoading

CatalogueStore
  systems
  subsystems
  archetypes
  genericSolutions
  selection

MarketplaceStore
  filters
  results
  lookups

ManufacturerSolutionsStore
  solutions
  currentSolution
  assets

AdminReviewStore
  queue
  selectedId
```

Do not persist server entities into browser storage as a second database.

Only authentication tokens need persistence in v1.

---

## 20. Data consistency and concurrency

The backend does not expose ETags/version numbers.

Therefore use conservative refresh behavior:

- refresh solution after mutation;
- refresh asset list after upload/delete;
- refresh submitted queue after approve/reject;
- refresh on workflow conflicts;
- do not assume a button enabled from stale client state guarantees the action remains valid.

Avoid optimistic mutation for workflow transitions in v1.

---

## 21. Security model

Frontend security is not authorization.

The browser may:

- hide unauthorized navigation;
- prevent obviously invalid workflow actions;
- validate form shape;
- preserve tokens only for the current tab/session.

The backend must still enforce:

- identity;
- role;
- manufacturer ownership;
- public visibility;
- IFC validity;
- workflow transitions;
- upload validation.

Never embed secrets in Angular environment files.

Do not log access/refresh tokens.

Avoid inserting untrusted HTML from JSONB fields. Render text via Angular bindings, not `innerHTML`, unless content is explicitly sanitized and there is a documented need.

External manufacturer `website` links should use safe link handling (`rel="noopener noreferrer"` for new-tab links).

---

## 22. Development networking

Application services should use relative URLs such as:

```text
/api/v1/systems
```

Example dev proxy:

```json
{
  "/api": {
    "target": "http://localhost:5000",
    "secure": false,
    "changeOrigin": true
  }
}
```

Exact backend port must match the developer's backend process/container setup.

Using a proxy avoids development CORS friction. If direct cross-origin calls are used, configure the backend `CORS_ORIGINS` to the Angular dev origin.

---

## 23. Deployment topology

Recommended production topology:

```text
Browser
   ↓ HTTPS
Reverse proxy
   ├── /        → Angular static files
   └── /api/*   → Flask/Gunicorn backend
```

Benefits:

- same origin;
- simple API base path;
- reduced CORS configuration;
- independent frontend/backend deployment artifacts;
- framework-independent IFC viewer remains client-side.

---

## 24. Testing architecture

### Unit

Test pure and framework boundaries:

- DTO/payload mappers;
- workflow selectors;
- technical JSON formatting;
- auth storage;
- API error normalization;
- query-param/filter conversion.

### Angular integration

Test:

- route guards;
- interceptor header attachment;
- one-at-a-time token refresh;
- API service routes/payloads;
- reactive form validation;
- components with loading/error/empty states.

### IFC package

Test:

- initialize/load/dispose sequencing;
- rejecting load before initialize if that is the chosen contract;
- safe repeated clear/dispose;
- model byte input and event callbacks.

Mock heavy browser/worker/GPU APIs in unit tests. Use a real browser smoke test for actual That Open initialization.

### End-to-end

Primary business path:

```text
manufacturer login
→ create DRAFT
→ upload valid IFC
→ submit
→ admin login
→ review + approve
→ anonymous marketplace contains solution
→ IFC asset loads publicly
```

Also test rejection/edit/resubmission when time allows.

---

## 25. Architecture decisions

### ADR-001 — Angular for application shell

**Decision:** Angular 22.x.

**Reason:** VIVA requires routing, role guards, typed HTTP, forms, file workflows, feature state, and multiple authenticated work areas. Angular provides these coherently without requiring a custom application framework.

### ADR-002 — IFC viewer is plain TypeScript

**Decision:** That Open integration lives outside Angular.

**Reason:** BIM visualization should be reusable and replaceable independently of the SPA framework. It also isolates a fast-moving 3D dependency surface.

### ADR-003 — IFC transport is outside viewer

**Decision:** API layer downloads bytes; viewer receives `Uint8Array`.

**Reason:** prevents JWT/backend coupling and makes the viewer work with local files or other storage later.

### ADR-004 — Backend is workflow authority

**Decision:** frontend mirrors workflow for UX but never substitutes it.

**Reason:** permissions and concurrent changes cannot be trusted to client state.

### ADR-005 — Heterogeneous data remains heterogeneous

**Decision:** generic recursive technical-data renderers; no category-specific fixed frontend schema in v1.

**Reason:** backend uses JSONB intentionally and exposes no commercial form schema endpoint.

### ADR-006 — No NgRx in v1

**Decision:** Signals + feature services/stores.

**Reason:** state complexity does not justify a global event/reducer architecture yet.

### ADR-007 — Admin review is master/detail queue

**Decision:** one `/admin/review` feature based on submitted-list endpoint.

**Reason:** backend has no direct admin detail endpoint.

### ADR-008 — Session storage for current JWT contract

**Decision:** tokens stored behind a session-scoped abstraction for v1.

**Reason:** current backend requires the refresh token in a JSON body. This can later migrate to an HttpOnly cookie if the backend contract changes.

---

## 26. Known backend constraints that affect frontend design

The first frontend must account for these current constraints:

1. list endpoints are not paginated;
2. no text search API exists;
3. marketplace responses do not embed manufacturer/generic display data;
4. `generic_solution_id` cannot be changed after commercial creation;
5. no generic commercial form-schema API exists;
6. no logout/revocation API exists;
7. no admin taxonomy/manufacturer/audit endpoints exist;
8. no dedicated admin commercial-detail endpoint exists;
9. upload size is environment-configurable and not exposed by an API endpoint;
10. assets are streamed as downloads rather than specialized BIM streaming endpoints.

Do not hide these constraints behind fabricated client APIs.

---

## 27. Evolution points

Future versions may add, without invalidating the core architecture:

- backend-driven commercial form schemas;
- pagination/search/sorting;
- richer nested marketplace DTOs;
- HttpOnly refresh-cookie authentication;
- thumbnails/previews;
- server-produced Fragments for faster BIM loading;
- advanced That Open selection/properties/clipping/measurement features;
- admin catalogue/manufacturer management;
- audit-log UI;
- server-side asset range/caching improvements.

Those should be separate iterations after the current end-to-end flow works.
