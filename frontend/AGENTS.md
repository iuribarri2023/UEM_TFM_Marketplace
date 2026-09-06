# AVRA VIVA Marketplace Frontend — Agent Instructions

## 1. Project scope

This repository contains the **web frontend** for AVRA VIVA Marketplace.

AVRA VIVA Marketplace lets users browse AVRA generic construction solutions, inspect their technical/BIM information, discover approved manufacturer-specific commercial solutions, and lets authenticated manufacturers submit commercial solutions for administrator review.

The frontend consumes the existing Flask backend exclusively through its versioned REST API:

```text
/api/v1
```

The frontend must not reimplement backend business rules as an alternative source of truth. It may mirror backend rules to improve UX, but the backend remains authoritative.

Do not introduce React, Next.js, Vue, or server-side application logic into this repository.

The chosen application framework is **Angular 22.x with TypeScript**, using standalone APIs. The IFC/BIM viewer must remain a **framework-independent TypeScript package** built around That Open Company libraries.

---

## 2. Sources of truth and precedence

Before changing architecture or API integration, read:

```text
AGENTS.md
ARCHITECTURE.md
```

When the backend repository is available, also inspect:

```text
backend/AGENTS.md
backend/ARCHITECTURE.md
backend/docs/openapi.yaml
backend/app/api/v1/
backend/app/schemas/
backend/app/services/
backend/tests/api/
```

For backend compatibility, prefer the **running backend and current backend code** over assumptions in frontend code or prose documentation.

Instruction precedence:

1. explicit user instruction for the current task;
2. this `AGENTS.md`;
3. `ARCHITECTURE.md`;
4. backend `docs/openapi.yaml`;
5. existing frontend implementation details.

If the backend contract and an older frontend assumption conflict, update the frontend. Do not silently modify the backend to accommodate invented frontend contracts.

---

## 3. Non-negotiable architecture

The frontend has two primary parts:

```text
Angular application shell
+
framework-independent IFC viewer package
```

Expected dependency direction:

```text
Angular pages/components
        ↓
Angular feature services/stores
        ↓
Angular API services
        ↓
HTTP /api/v1
        ↓
Flask backend
```

and separately:

```text
Angular IFC host component
        ↓
VivaIfcViewer (plain TypeScript)
        ↓
That Open Company libraries
        ↓
Three.js / WebIFC / Fragments
```

The IFC package must not import from `@angular/*`.

The IFC package must not know about JWTs, Flask, REST routes, Angular `HttpClient`, application roles, or VIVA workflow states.

The application layer downloads IFC bytes and passes a `Uint8Array` to the viewer.

---

## 4. Recommended repository structure

Prefer a workspace layout equivalent to:

```text
frontend/
├── AGENTS.md
├── ARCHITECTURE.md
├── package.json
├── package-lock.json
├── apps/
│   └── viva-web/
│       ├── angular.json
│       ├── proxy.conf.json
│       └── src/
│           └── app/
│               ├── core/
│               ├── shared/
│               └── features/
└── packages/
    ├── viva-contracts/
    └── viva-ifc-viewer/
```

`viva-contracts` must contain framework-neutral TypeScript types only.

`viva-ifc-viewer` must be a plain TypeScript browser library.

Do not create an Angular library for the IFC engine if doing so introduces Angular dependencies into it.

---

## 5. Angular rules

Use current Angular 22 standalone architecture.

Prefer:

- strict TypeScript;
- standalone components;
- lazy-loaded feature routes;
- `inject()` where it makes code clearer;
- Signals for local/feature state;
- RxJS for HTTP and event streams;
- Angular `HttpClient` for API calls;
- functional HTTP interceptors;
- reactive forms for application forms;
- native Angular control-flow syntax in new templates;
- `ChangeDetectionStrategy.OnPush` when not already the project default;
- route guards for role-protected areas.

Do not add NgRx for the first version unless a concrete requirement justifies it.

Do not put raw HTTP calls in presentation components.

Do not put role/workflow decisions in templates when they can be represented by named selectors/helpers.

Avoid global mutable state.

---

## 6. Backend response contract

All JSON success responses from `/api/v1` are wrapped as:

```json
{
  "data": {}
}
```

or:

```json
{
  "data": []
}
```

All application errors are wrapped as:

```json
{
  "error": {
    "code": "SOME_ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

Create shared contracts equivalent to:

```ts
export interface ApiEnvelope<T> {
  data: T;
}

export interface ApiErrorBody {
  code: string;
  message: string;
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody;
}
```

Do not assume unwrapped JSON payloads.

Dates arrive as ISO date-time strings. UUIDs arrive as strings.

---

## 7. Canonical backend endpoints

The frontend must use the routes that exist today. Do not invent endpoints.

### Public catalogue

```text
GET /api/v1/systems
GET /api/v1/systems/{id}
GET /api/v1/systems/by-code/{code}

GET /api/v1/subsystems?system_id={uuid}
GET /api/v1/subsystems/{id}
GET /api/v1/subsystems/by-code/{code}

GET /api/v1/archetypes?subsystem_id={uuid}
GET /api/v1/archetypes/{id}
GET /api/v1/archetypes/by-code/{code}

GET /api/v1/generic-solutions?archetype_id={uuid}
GET /api/v1/generic-solutions/{id}
GET /api/v1/generic-solutions/by-code/{code}
```

Generic-solution detail responses include `slots` and `assets`.

### Public marketplace

```text
GET /api/v1/marketplace/commercial-solutions
GET /api/v1/marketplace/commercial-solutions/{id}
GET /api/v1/manufacturers
GET /api/v1/manufacturers/{id}
```

Supported marketplace filters are:

```text
generic_solution_id
archetype_id
subsystem_id
system_id
manufacturer_id
```

Only `APPROVED` commercial solutions are public.

### Authentication

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### Manufacturer workspace

```text
GET    /api/v1/manufacturer/commercial-solutions
POST   /api/v1/manufacturer/commercial-solutions
GET    /api/v1/manufacturer/commercial-solutions/{id}
PATCH  /api/v1/manufacturer/commercial-solutions/{id}
DELETE /api/v1/manufacturer/commercial-solutions/{id}
POST   /api/v1/manufacturer/commercial-solutions/{id}/submit

GET    /api/v1/manufacturer/commercial-solutions/{id}/assets
POST   /api/v1/manufacturer/commercial-solutions/{id}/assets
DELETE /api/v1/manufacturer/commercial-solutions/{id}/assets/{asset_id}
```

### Asset download

```text
GET /api/v1/assets/{id}/download
```

### Administrator review

```text
GET  /api/v1/admin/commercial-solutions/submitted
POST /api/v1/admin/commercial-solutions/{id}/approve
POST /api/v1/admin/commercial-solutions/{id}/reject
```

There is currently **no dedicated admin commercial-solution detail endpoint**, taxonomy CRUD endpoint, manufacturer admin endpoint, audit-log endpoint, logout endpoint, or archive endpoint.

Do not build frontend features that require those missing endpoints unless the user explicitly asks to change the backend as a separate task.

---

## 8. Canonical TypeScript domain contracts

Keep frontend DTOs aligned with the backend Pydantic schemas.

At minimum define:

```text
SystemDto
SubsystemDto
ArchetypeDto
GenericSolutionSummaryDto
GenericSolutionDto
GenericSolutionSlotDto
AssetDto
ManufacturerDto
CommercialSolutionDto
CurrentUserDto
TokenResponseDto
```

Important shapes:

```ts
export interface CurrentUserDto {
  id: string;
  email: string;
  role: 'ADMIN' | 'MANUFACTURER';
  manufacturer_id: string | null;
}

export interface TokenResponseDto {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
```

Commercial solution create payload:

```ts
export interface CommercialSolutionCreateDto {
  generic_solution_id: string;
  code: string;
  name_es: string;
  description?: string | null;
  technical_data?: Record<string, unknown>;
}
```

Commercial solution patch payload may contain only:

```text
code
name_es
description
technical_data
```

`generic_solution_id` is not patchable with the current backend.

Never send `manufacturer_id`, `status`, `created_by`, `updated_by`, `submitted_at`, `approved_at`, `approved_by`, or `assets` in create/update payloads.

Manufacturer ownership is derived by the backend from the authenticated user.

---

## 9. Authentication rules

The backend uses bearer JWT authentication.

Login payload:

```json
{
  "email": "user@example.com",
  "password": "..."
}
```

Refresh payload:

```json
{
  "refresh_token": "..."
}
```

Authenticated requests use:

```text
Authorization: Bearer <access_token>
```

For the current backend contract, persist the token pair in `sessionStorage` so a page reload can restore the session. Encapsulate storage behind an auth-token store; components must not access `sessionStorage` directly.

On application startup, if tokens exist, call `/auth/me` to restore/validate the session.

On a 401 from an authenticated API request:

1. perform at most one refresh request for all concurrent 401s;
2. store the returned token pair;
3. retry the original request once;
4. if refresh fails, clear session state and route to login.

Never refresh recursively on `/auth/login` or `/auth/refresh` failures.

Do not decode JWT claims to determine authoritative user state. Use `/auth/me`.

---

## 10. Roles and route protection

The backend roles are exactly:

```text
ADMIN
MANUFACTURER
```

Public pages require no authentication.

Manufacturer pages require `MANUFACTURER`.

Admin review pages require `ADMIN`.

A route guard improves UX, but backend 401/403 responses remain authoritative.

Do not show manufacturer actions to an admin merely because the admin is authenticated. The backend intentionally returns 403 when an admin calls manufacturer-only endpoints.

---

## 11. Commercial-solution workflow

Canonical statuses:

```text
DRAFT
SUBMITTED
APPROVED
REJECTED
ARCHIVED
```

Backend rules:

| Status | Manufacturer edit metadata | Change assets | Submit | Delete |
|---|---:|---:|---:|---:|
| `DRAFT` | yes | yes | yes, if valid IFC exists | yes |
| `SUBMITTED` | no | no | no | no |
| `APPROVED` | yes; edit resets to `DRAFT` | only after metadata edit has reset it to `DRAFT` | no until reset | no |
| `REJECTED` | yes; edit resets to `DRAFT` | yes | yes, if valid IFC exists | yes |
| `ARCHIVED` | no | no | no | no |

The frontend should mirror these rules for button visibility/disabled states.

Do not assume UI checks are sufficient. Always handle `INVALID_WORKFLOW_TRANSITION` and refresh stale data after a rejected transition.

Editing an `APPROVED` or `REJECTED` solution clears review metadata and returns it to `DRAFT` on the backend.

Submitting a solution requires at least one linked asset with:

```text
format == "ifc"
validation_data.valid == true
```

The backend, not the browser viewer, decides whether an IFC is valid for submission.

---

## 12. Asset and IFC rules

Upload endpoint is `multipart/form-data`.

Required field:

```text
file
```

Optional fields:

```text
code
role
asset_type
```

Backend defaults are:

```text
role = primary_commercial_model
asset_type = bim_model
```

The storage layer currently accepts these file extensions:

```text
.ifc
.pdf
.png
.jpg
.jpeg
.webp
```

Only IFC files receive IfcOpenShell inspection/validation metadata.

Do not hard-code the backend upload limit as an invariant because it is environment-configurable. The current backend default is 10 MiB. Handle both:

```text
413 FILE_TOO_LARGE
400 VALIDATION_FAILED
```

Asset download authorization is important:

- assets linked to generic solutions are public;
- assets linked to an `APPROVED` commercial solution are public;
- an admin may download private commercial assets when authenticated;
- a manufacturer may download assets belonging to its own solutions when authenticated;
- unauthenticated download of non-public commercial assets returns 403.

When a token is available, authenticated asset downloads must include the bearer token.

---

## 13. Framework-independent IFC viewer

The package `packages/viva-ifc-viewer` must expose a small application-owned API and hide That Open implementation details from Angular.

A suitable starting interface is:

```ts
export interface VivaIfcModelInput {
  id: string;
  name: string;
  bytes: Uint8Array;
}

export interface VivaIfcViewerOptions {
  background?: 'light' | 'dark';
}

export interface VivaIfcViewer {
  initialize(container: HTMLElement, options?: VivaIfcViewerOptions): Promise<void>;
  load(model: VivaIfcModelInput): Promise<void>;
  clear(): Promise<void>;
  fitToModel(): Promise<void> | void;
  dispose(): Promise<void> | void;
}
```

Additional selection, property, visibility, clipping, and measurement functions may be added behind this interface.

Rules:

- Angular performs HTTP downloads.
- Angular converts `ArrayBuffer` to `Uint8Array`.
- The viewer receives bytes, not a backend URL.
- The viewer does not access auth storage.
- The viewer does not use Angular dependency injection.
- The viewer cleans up renderer resources, workers, listeners, models, and Three.js resources on `dispose()`.
- Prefer current official That Open APIs from `@thatopen/components`, `@thatopen/components-front`, `@thatopen/fragments`, `three`, and `web-ifc` as required by compatible package versions.
- Pin compatible package versions in the lockfile; do not mix incompatible That Open package generations.

Do not copy That Open implementation throughout Angular components. There should be one thin Angular host adapter.

---

## 14. Heterogeneous technical data

Generic solutions contain heterogeneous JSON sections:

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

Slots contain:

```text
key
name_es
role
sequence
required
properties
metrics
source_reference
```

Commercial solutions contain arbitrary:

```text
technical_data: Record<string, unknown>
```

Do not create a fixed SQL-like frontend model with hard-coded properties for only one construction family.

Build reusable JSON/technical-data presentation components capable of rendering nested objects, arrays, scalar values, units, source/status metadata, and empty states.

For the first manufacturer editor, a validated JSON-object editor for `technical_data` is acceptable and preferable to inventing a form schema the backend does not expose.

---

## 15. Frontend route scope for v1

Implement at least:

```text
/
/catalogue
/generic-solutions/:code
/marketplace
/marketplace/:id
/manufacturers
/manufacturers/:id
/login
/manufacturer/solutions
/manufacturer/solutions/new
/manufacturer/solutions/:id/edit
/admin/review
```

The admin review UI should work from `/admin/review` because the current backend has a submitted-list endpoint but no dedicated admin detail endpoint. A master/detail layout on that page is appropriate.

Do not require unsupported backend routes for deep linking.

---

## 16. API service responsibilities

Prefer focused API services such as:

```text
AuthApi
CatalogueApi
MarketplaceApi
ManufacturerSolutionsApi
AdminReviewApi
AssetApi
```

Each API service:

- knows endpoint paths;
- sends correctly shaped payloads;
- unwraps `ApiEnvelope<T>` in one consistent manner;
- does not own view-specific state;
- does not swallow API errors.

Keep user-facing error conversion in a shared application error layer.

---

## 17. Feature state

Prefer small Signal-based stores/facades:

```text
AuthStore
CatalogueStore
MarketplaceStore
ManufacturerSolutionsStore
AdminReviewStore
```

A store may coordinate one feature's loading state, API calls, derived selectors, and errors.

Do not create one global store containing the entire application.

Keep HTTP Observables finite and avoid manual subscriptions where `async`, `toSignal`, or explicit lifecycle cleanup is more appropriate.

---

## 18. Error handling

Explicitly handle important backend codes:

```text
AUTHENTICATION_FAILED
PERMISSION_DENIED
ENTITY_NOT_FOUND
NOT_FOUND
VALIDATION_FAILED
INTEGRITY_ERROR
INVALID_WORKFLOW_TRANSITION
MISSING_IFC_FILE
INVALID_IFC_FILE
FILE_TOO_LARGE
STORAGE_ERROR
INTERNAL_SERVER_ERROR
```

Expected UX examples:

- `AUTHENTICATION_FAILED`: clear invalid session where appropriate and show login feedback;
- `PERMISSION_DENIED`: show a forbidden state, not a generic 500 error;
- `ENTITY_NOT_FOUND`: route/page not-found state;
- `MISSING_IFC_FILE`: tell manufacturer that a backend-valid IFC is required before submission;
- `INVALID_IFC_FILE`: display backend validation message beside upload;
- `INVALID_WORKFLOW_TRANSITION`: refresh the solution/queue because state may be stale;
- `FILE_TOO_LARGE`: preserve form state and explain upload failure;
- `INTEGRITY_ERROR`: show a non-destructive conflict message, commonly for duplicate constrained values such as codes.

Never display stack traces to users.

---

## 19. UX and accessibility

The first version must be usable on desktop and tablet widths and remain functional on mobile.

Requirements:

- semantic headings and landmarks;
- keyboard-operable navigation and actions;
- visible focus states;
- form labels and validation text;
- `aria-live` or equivalent for important async feedback;
- loading, empty, error, and success states;
- destructive-action confirmation;
- clear status badges for workflow states;
- BIM viewer controls accessible outside the canvas where practical;
- do not encode status using color alone.

Spanish domain field names such as `name_es` reflect the backend contract. The first UI may use Spanish or bilingual labels, but do not rename API fields in transport DTOs.

---

## 20. Testing requirements

Use the Angular CLI's current Vitest-based unit testing setup for the Angular application.

At minimum test:

- API envelope unwrapping;
- auth token restoration;
- refresh/retry behavior and refresh de-duplication;
- role guards;
- workflow action selectors;
- technical JSON renderer edge cases;
- create/update payload mapping;
- multipart asset upload construction;
- backend error-code mapping;
- IFC host lifecycle (`initialize`, `load`, `dispose`) with the viewer mocked.

For the plain TypeScript IFC package, test framework-independent lifecycle and input validation without requiring Angular TestBed.

Add a small end-to-end smoke suite when practical for:

1. public catalogue browse;
2. login;
3. manufacturer create → upload IFC → submit;
4. admin review → approve/reject;
5. approved solution appears in marketplace.

The backend should be treated as a real external contract in integration/E2E tests.

---

## 21. Development and deployment

Prefer same-origin API paths in application code:

```text
/api/v1/...
```

For local Angular development, configure an Angular dev-server proxy so `/api` targets the Flask backend. This avoids hard-coding backend origins in application services.

The backend sample environment currently allows `http://localhost:5173`; an Angular dev server commonly uses another port. Either use a matching frontend dev port or update backend `CORS_ORIGINS` as a deployment/configuration change. Do not work around CORS by disabling browser security.

For production, prefer:

```text
https://host/       -> Angular static application
https://host/api/   -> Flask/Gunicorn reverse proxy
```

Do not commit secrets or real JWTs.

---

## 22. Non-goals for first version

Unless explicitly requested, do not implement:

- React or another second SPA framework;
- SSR/SSG;
- micro-frontends;
- NgRx;
- offline-first synchronization;
- WebSockets;
- GraphQL;
- client-side IFC validity as a replacement for IfcOpenShell validation;
- admin taxonomy CRUD;
- admin manufacturer CRUD;
- audit-log UI;
- archive workflow;
- logout token revocation on the server;
- schema-specific manufacturer forms that the backend cannot describe;
- BCF, clash detection, federation, advanced measurements, or drawing extraction in the first BIM viewer milestone.

Keep the first version small enough to be demonstrable end-to-end.

---

## 23. Definition of done

A change is complete only when:

- it uses only backend endpoints that actually exist;
- request and response DTOs match current backend schemas;
- role and workflow behavior match backend enforcement;
- all authenticated calls use the bearer token correctly;
- IFC bytes are fetched outside the framework-independent viewer;
- the viewer package contains no Angular imports;
- loading/error/empty states are handled;
- relevant tests pass;
- TypeScript builds in strict mode;
- linting/formatting pass;
- no secrets, generated binaries, or local environment credentials are committed;
- `AGENTS.md` and `ARCHITECTURE.md` are updated if an intentional architectural decision changes.
