# Phase 7A — Frontend Architecture and Setup

**Date:** 2026-09-14
**Scope:** Establish a clean, minimal React + Vite frontend foundation — folder architecture, routing, a centralized API client, environment configuration, and placeholder pages — plus verify real backend connectivity. Architecture and setup only; no real UI, no state management, no authentication.

---

## 1. Purpose of Phase 7A

Phases 6A–6H completed and manually verified the entire backend (122 automated tests, plus a real-process HTTP/SQLite verification in Phase 6H). No frontend existed. Phase 7A's job is narrow: stand up a frontend project that can later grow into the real UI (Phases 7B–7H) and, eventually, multi-user/Supabase support (Phase 8) — without committing to any of that yet, and without touching backend business logic.

## 2. Frontend Technology Selected

**React 19 + Vite 8, plain JavaScript** (no TypeScript), scaffolded via `npm create vite@latest frontend -- --template react`. Router: `react-router-dom` (added as the only extra dependency beyond React itself).

## 3. Why React + Vite Was Selected

The task explicitly named React + Vite + JavaScript as the preferred stack and explicitly asked not to introduce TypeScript unless the existing project already strongly indicated it — it does not (the entire backend is Python; there is no prior frontend convention to match). Vite was used as-is rather than Create React App or a meta-framework (Next.js, Remix) because Phase 7A's own scope is "architecture and setup only" — Vite's plain dev server + client-side `react-router-dom` routing is the minimal tool that satisfies every Step 1–13 requirement without pulling in server-side rendering, file-based routing conventions, or other machinery this phase does not need.

## 4. Frontend Folder Architecture

```
frontend/
    .env.example          -- documented, git-tracked template
    .env                  -- developer-local, git-ignored (created for this phase's own verification)
    src/
        api/
            client.js          -- the ONLY module that calls fetch() directly
            procurementApi.js  -- healthCheck / analyzeProcurement / getProcurementRuns / getProcurementRun
        components/
            common/
                BackendStatusCheck.jsx   -- Step 9's connectivity check (temporary, clearly labeled)
            layout/
                Layout.jsx                -- minimal shell: header + nav + <Outlet/>
        config/
            env.js             -- single source of truth for VITE_API_BASE_URL
        pages/
            HomePage.jsx, AnalysisPage.jsx, ResultsPage.jsx, HistoryPage.jsx, NotFoundPage.jsx
        routes/
            AppRoutes.jsx       -- all route definitions
        styles/
            global.css          -- minimal reset + layout-shell styling only
        App.jsx                 -- <BrowserRouter><AppRoutes /></BrowserRouter>
        main.jsx                 -- React entry point (Vite-generated, import path updated)
```

**Deliberate deviation from the suggested structure:** a `src/utils/` folder was **not** created. Phase 7A introduces no shared formatting/calculation helper that would live there — creating it empty would violate this phase's own "do not create empty folders with no purpose" instruction. It will be added in a later phase (7D/7E) once real UI logic actually needs one.

## 5. Routing Architecture

`react-router-dom`'s `<BrowserRouter>` wraps a single `<Routes>` tree (`src/routes/AppRoutes.jsx`). One parent route renders `Layout` (header/nav + `<Outlet/>`); five child routes render the placeholder pages:

| Path | Component |
|---|---|
| `/` | `HomePage` |
| `/analyze` | `AnalysisPage` |
| `/results` | `ResultsPage` |
| `/history` | `HistoryPage` |
| `*` (any unmatched path) | `NotFoundPage` |

Every placeholder page renders only an `<h1>` identifying itself (e.g. "Home Page — Phase 7A Placeholder") — no real UI, per this phase's explicit scope limit. `NotFoundPage` additionally has a link back to `/`.

## 6. API Communication Architecture

Two layers, matching the task's "API calls must be centralized" rule:
- **`src/api/client.js`** — the single `fetch()` call site in the whole frontend. Exposes `get(path)`/`post(path, data)`, reads `API_BASE_URL` from `src/config/env.js`, attaches JSON headers, and normalizes both network failures and non-2xx HTTP responses into a single `Error` type (no raw fetch `Response`/`TypeError` objects leak past this module).
- **`src/api/procurementApi.js`** — one function per existing backend endpoint, calling the exact existing paths (verified against `backend/api/routes/procurement.py` and `backend/api/main.py` — Section 1 of this report's inspection step): `healthCheck()` → `GET /health`; `analyzeProcurement(runInput)` → `POST /procurement/analyze`; `getProcurementRuns()` → `GET /procurement/runs`; `getProcurementRun(runId)` → `GET /procurement/runs/{run_id}`. No new endpoint was invented; no endpoint path was altered.

Neither module contains any procurement calculation (distance, savings, MOQ, freshness, group formation, or decision logic) — confirmed by inspection: both files import only `fetch` (via the browser) and `../config/env`; nothing from `backend/` is imported (the frontend cannot import Python).

## 7. Environment Variable Strategy

`src/config/env.js` is the single place `import.meta.env.VITE_API_BASE_URL` is read; it falls back to `http://127.0.0.1:8731` if unset, and every other module imports `API_BASE_URL` from there — no component or API module reads `import.meta.env` directly, and no URL is hardcoded elsewhere. `frontend/.env.example` documents the variable (`VITE_API_BASE_URL=http://127.0.0.1:8731`, matching the exact value this phase's own instructions specified) and is git-tracked; `frontend/.env` (created locally for this phase's own verification, holding the same value) is git-ignored (Section 11).

## 8. Backend/Frontend Separation

`frontend/` was created as a sibling of `backend/`, `data/`, `reports/`, `tests/` at the project root — no existing folder was moved or renamed. The two run as fully independent processes (`uvicorn backend.api.main:app` and `npm run dev`, Section 12); the frontend has no build-time or run-time dependency on Python, and the backend has no dependency on Node. No backend business-logic file (`backend/core/`, `backend/models/`, `backend/services/`, `backend/persistence/`) was touched. `backend/api/main.py` was modified for exactly one reason: CORS (Section 9) — no other change was made there or anywhere else under `backend/api/`.

## 9. CORS Findings

**Inspected first, per this phase's explicit instruction, before changing anything.** `grep -r "CORS\|cors" backend/` returned no matches — the backend had no `CORSMiddleware` at all. Without it, a browser tab served from the Vite dev server (a different origin than the backend) would block every response from `src/api/client.js`, even though the HTTP request itself would reach the server — verified directly: a simulated cross-origin `GET /health` **without** an `Origin` header allow-listed returned no `access-control-allow-origin` header.

This phase's own architecture pre-authorizes exactly this: "*Do NOT modify: ...backend/api/ unless absolutely required for frontend connectivity*." It is required here because `frontend/.env`'s `VITE_API_BASE_URL` design (an explicit, direct absolute backend URL, per this phase's own instructions) means the browser talks directly to the FastAPI process — a same-origin Vite dev-server proxy (which would have avoided CORS entirely) would have contradicted that explicitly-specified `.env` design.

**Minimal change made:** `backend/api/main.py` — added `from fastapi.middleware.cors import CORSMiddleware` and `app.add_middleware(CORSMiddleware, allow_origins=LOCAL_FRONTEND_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])`, where `LOCAL_FRONTEND_ORIGINS` is an explicit, finite list — **not** `allow_origins=["*"]`:
```python
LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",   # Vite's true default port
    "http://localhost:5174", "http://127.0.0.1:5174",   # Vite's auto-increment fallback (see below)
]
```
Port 5174 was added in addition to Vite's documented default (5173) because, while verifying this phase, port 5173 on this machine was already held by an unrelated, pre-existing Vite dev server for a different local project (`IGNITING-MINDS-prototpye-1-main`, confirmed via `netstat`/`Get-CimInstance Win32_Process` inspection and deliberately **not** touched — killing another project's process would be well outside this phase's scope). Vite automatically fell back to port 5174 in that situation, which is standard Vite behavior any developer's machine could hit. Both ports are still explicit local-development-only origins, not a wildcard. No production CORS policy was written (none is needed — there is no production deployment yet).

Verified live (Section 10): both the simple request and the CORS preflight (`OPTIONS`) for `POST /procurement/analyze` returned the correct `access-control-allow-origin` header for the frontend's actual origin. The full backend regression suite (122 tests) was re-run after this change and remained 122/122 passing — the change affects only cross-origin header behavior, nothing in any tested code path.

## 10. Connectivity Verification

Performed against **real, separately-running processes** (not mocks):

1. Started the backend: `uvicorn backend.api.main:app --host 127.0.0.1 --port 8731` (via `python -m uvicorn`, since the `uvicorn` console script was not on this shell's `PATH` — a shell detail, not an app defect). `GET /health` → `200 {"status":"ok"}`.
2. Started the frontend: `npm run dev` → Vite served on `http://localhost:5174` (port 5173 unavailable, see Section 9).
3. `npm run build` completed with **zero errors** (35 modules transformed, valid production bundle produced) — strong evidence every import, JSX file, and route definition is structurally correct.
4. Confirmed `VITE_API_BASE_URL` (`127.0.0.1:8731`) is present in the built JS bundle — proves `config/env.js` correctly reads the environment variable end-to-end.
5. Requested all 5 routes (`/`, `/analyze`, `/results`, `/history`, `/some-invalid-route`) from the running dev server: all returned `200` with the correct `<title>Collaborative Procurement Decision-Support System</title>` shell (Vite's dev server always serves `index.html` for client-side-routed paths; React Router then matches the path in-browser, including the wildcard `*` → `NotFoundPage`).
6. Simulated the exact cross-origin requests a browser tab at `http://localhost:5174` would make: a simple `GET /health` and a CORS preflight `OPTIONS /procurement/analyze` — both returned `access-control-allow-origin: http://localhost:5174`, confirming the browser would be permitted to read the response (this is the server-side condition a browser's CORS enforcement checks; it is the correct way to verify CORS behavior without a GUI browser).
7. Re-ran the full backend test suite: **122 passed, 0 failed, 0 skipped** — unchanged.
8. Both dev processes were stopped cleanly at the end of verification (backend and frontend); nothing was left running.

**Limitation, stated honestly:** no headless-browser tool (e.g. Playwright) was installed to literally render the DOM and click through links — doing so would have required adding a new dependency and a real browser download, disproportionate to an "architecture and setup" phase. The evidence above (clean production build, correct per-route HTTP responses, correct CORS headers for the real frontend origin) is strong indirect confirmation that the React application loads and routes correctly; a one-time manual click-through (`npm run dev`, visit each route in an actual browser) is recommended as an easy final human check but was not performed here.

## 11. Dependencies Installed

| Package | Version constraint | Reason |
|---|---|---|
| `react`, `react-dom` | `^19.2.8` (Vite template default) | Core framework |
| `react-router-dom` | latest (`^7.x`, installed via `npm install react-router-dom`) | Routing foundation (Step 5) |
| `vite`, `@vitejs/plugin-react` | Vite template defaults | Dev server / build tool |
| `oxlint` | Vite template default | Linting (template default, not added by this phase) |

`npm install` reported **0 vulnerabilities**. Explicitly **not** installed: any UI framework (Material UI, Ant Design, Bootstrap, Tailwind), any state-management library (Redux, Zustand), Supabase, Firebase — confirmed by inspecting `frontend/package.json`'s final dependency list, which contains only the packages above.

## 12. Commands to Run Frontend

```
# Backend (from the project root)
uvicorn backend.api.main:app --reload --port 8731
# (use `python -m uvicorn ...` if the uvicorn script isn't on PATH)

# Frontend (from frontend/)
cd frontend
cp .env.example .env      # first time only
npm install
npm run dev
```
Vite prints its actual local URL on startup (normally `http://localhost:5173`, or the next free port if that one is taken locally).

## 13. Files Created

- `frontend/` — full Vite-scaffolded project (23 git-trackable files: `package.json`, `package-lock.json`, `vite.config.js`, `index.html`, `.gitignore`, `.oxlintrc.json`, `README.md`, `public/favicon.svg`, plus everything under `src/` listed in Section 4) and `.env.example`
- `frontend/.env` — developer-local, git-ignored, not part of the committed project
- `reports/phase7a_frontend_architecture_and_setup.md` — this report

## 14. Files Modified

- `backend/api/main.py` — added `CORSMiddleware` with an explicit local-origin allow-list (Section 9). This is the **only** backend file touched in this phase.

No file under `backend/core/`, `backend/models/`, `backend/services/`, `backend/persistence/`, `data/`, `research/`, or any prior `reports/`/`tests/` file was changed. The root `.gitignore` was inspected but **not** modified — its existing bare `.env` pattern already ignores `frontend/.env` (verified with `git check-ignore -v frontend/.env`), and Vite's own auto-generated `frontend/.gitignore` already ignores `frontend/node_modules/` and `frontend/dist/`; `frontend/.env.example` is correctly **not** ignored by either file (all three verified directly, not assumed).

## 15. Explicitly Deferred Features

Per this phase's own scope list, **not** implemented: real dashboard UI, final visual design, charts, vendor input forms, the procurement analysis workflow, results visualization, run-history UI, authentication, login/signup/logout, user accounts, Supabase, Firebase, PostgreSQL, any cloud database, Redux/Zustand or any global client-side state management, any backend redesign, and any ML integration. `src/api/procurementApi.js`'s functions are defined but are called from exactly one place (`BackendStatusCheck.jsx`'s `healthCheck()`, for Step 9's connectivity check only) — `analyzeProcurement`, `getProcurementRuns`, and `getProcurementRun` are not yet called from any page, matching this phase's "do not call these functions from real pages yet unless needed for connectivity verification" instruction.

---

**Files/directories read for this phase:** project root listing, `.gitignore`, `requirements.txt`, `backend/api/main.py`, `backend/api/routes/procurement.py`, `backend/api/schemas.py`, `backend/api/serialization.py`, `backend/api/dependencies.py`, `reports/phase6f_fastapi_api.md`, `reports/phase6g_database_persistence.md`, `reports/phase6h_manual_api_integration_verification.md`.
**Files created:** see Section 13. **Files modified:** `backend/api/main.py` only.
