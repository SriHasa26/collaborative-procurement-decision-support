// Phase 7A -- centralized functions for the EXISTING backend API
// (backend/api/routes/procurement.py, backend/api/main.py). Every path
// below matches an already-implemented, already-verified (Phase 6H)
// endpoint exactly -- no new endpoint is invented here, and none of these
// functions perform any decision-support calculation themselves; they only
// forward requests/responses through backend/api/client.js.

import { get, post } from "./client";

// GET /health
export function healthCheck() {
  return get("/health");
}

// POST /procurement/analyze
// `runInput` must already match the backend's ProcurementAnalysisRequest
// shape (backend/api/schemas.py) -- this function does not validate,
// transform, or compute anything about it.
export function analyzeProcurement(runInput) {
  return post("/procurement/analyze", runInput);
}

// GET /procurement/runs
export function getProcurementRuns() {
  return get("/procurement/runs");
}

// GET /procurement/runs/{run_id}
export function getProcurementRun(runId) {
  return get(`/procurement/runs/${encodeURIComponent(runId)}`);
}
