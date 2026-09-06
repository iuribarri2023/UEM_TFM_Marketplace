# AVRA VIVA Marketplace Frontend

Angular 22 SPA for the AVRA VIVA Marketplace Flask API. The frontend uses only relative `/api/v1` URLs and expects the backend response envelope:

```json
{ "data": {} }
```

Application errors are normalized from:

```json
{ "error": { "code": "ERROR_CODE", "message": "Human readable message" } }
```

## Structure

```text
apps/viva-web/                  Angular SPA
packages/viva-contracts/        Framework-neutral DTOs and workflow helpers
packages/viva-ifc-viewer/       Framework-neutral That Open IFC viewer wrapper
```

`viva-ifc-viewer` has no Angular imports. Angular downloads `/api/v1/assets/{id}/download` as `arraybuffer`, converts it to `Uint8Array`, and passes bytes into the viewer.

## Backend prerequisite

Run the Flask backend locally before using the SPA. The Angular dev server proxies `/api` to:

```text
http://localhost:5000
```

Adjust `apps/viva-web/proxy.conf.json` only if your Flask process uses another port.

## Install

```bash
npm install
```

Pinned versions include Angular `22.1.x`, That Open Components `3.4.8`, Fragments `3.4.7`, Three `0.182.0`, and WebIFC `0.0.77`.

## Develop

```bash
npm start
```

Open the Angular dev server URL shown by the CLI. API calls stay same-origin through the dev proxy.

## Build

```bash
npm run build
```

## Test

```bash
npm run test
npm run test:packages
```

## Demo Flows

Public:

1. Open `/catalogue`.
2. Select System, Subsystem, Archetype.
3. Open a generic solution and preview an IFC asset.
4. Open `/marketplace`, filter approved commercial solutions, and inspect a commercial IFC.

Manufacturer:

1. Login at `/login` with a manufacturer account.
2. Open `/manufacturer/solutions`.
3. Create a draft at `/manufacturer/solutions/new`.
4. Edit backend-supported metadata and `technical_data`.
5. Upload assets, including an IFC, from the edit screen.
6. Preview the IFC and submit for review.
7. Rejected solutions show backend rejection feedback and can be edited again.

Admin:

1. Login at `/login` with an admin account.
2. Open `/admin/review`.
3. Select a submitted item from the queue.
4. Inspect metadata, technical data, assets, and IFC.
5. Approve or reject with a required reason.
6. Approved commercial solutions appear in the public marketplace.

## Backend Constraints Reflected in UI

There is no admin detail endpoint, so `/admin/review` is a queue/detail screen based on `GET /api/v1/admin/commercial-solutions/submitted`.

There is no logout endpoint; ending a session clears session-scoped browser tokens only.

The backend does not expose an upload-size endpoint. The UI handles `FILE_TOO_LARGE` and validation errors returned by the server instead of enforcing a hard-coded business limit.
