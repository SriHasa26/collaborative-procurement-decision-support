"""
Phase 6F -- FastAPI application entry point.
Phase 7A -- minimal CORS configuration for local frontend development only
(see reports/phase7a_frontend_architecture_and_setup.md, Section 9).

This module contains NO business logic. It only:
  1. Declares the FastAPI application (title/description/version).
  2. Registers the /health route.
  3. Includes the /procurement router (backend/api/routes/procurement.py).
  4. Allows cross-origin requests from the local Vite dev server only.

The description is deliberately truthful about what this project is:
a rule-based, deterministic decision-support system built on Phase
2A/2B/5D/5E's own mathematical and graph-based algorithms -- NOT an
AI-powered or ML-forecasting product. Phase 5C's own closed research
finding (simple statistical baselines matched or outperformed the tested
ML model on the project's held-out Potato test period) remains the
project's conclusion and is not reopened or contradicted here.

CORS NOTE (Phase 7A Step 10): the frontend calls this API directly via an
absolute base URL (frontend/.env's VITE_API_BASE_URL), not through a
same-origin dev-server proxy -- so without CORS the browser blocks every
response from frontend/src/api/client.js, even though the request itself
reaches this server. This is the ONLY reason CORSMiddleware was added:
it allows exactly the two equivalent local Vite dev origins
(http://localhost:5173 and http://127.0.0.1:5173 -- browsers treat these
as distinct origins), never a wildcard, and never anything else.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import procurement

LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Vite auto-increments to 5174 whenever 5173 is already bound by
    # another process on the machine (observed directly while verifying
    # this phase) -- included so a developer is not blocked by an
    # unrelated local port collision. Still an explicit, finite list of
    # local dev origins, never a wildcard.
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

APP_DESCRIPTION = (
    "A rule-based collaborative procurement decision-support system for street "
    "vendors. Validates vendor submissions, estimates demand, checks geographic "
    "compatibility, forms candidate purchasing groups, and evaluates each group "
    "against deterministic cost, savings, MOQ, and freshness rules to recommend "
    "collaborative group purchases. This system is NOT AI-powered and performs no "
    "ML-based forecasting: prior research on this project found that simple "
    "statistical baselines matched or outperformed the tested ML model on the "
    "project's own held-out test data, so no ML component is used in this pipeline."
)

app = FastAPI(
    title="Collaborative Procurement Decision-Support API",
    description=APP_DESCRIPTION,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", summary="Health check")
def health() -> dict:
    """Confirms the API process is running. No database or external
    dependency exists in this project, so there is nothing further to
    check here."""
    return {"status": "ok"}


app.include_router(procurement.router)
