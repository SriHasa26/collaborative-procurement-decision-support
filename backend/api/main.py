"""
Phase 6F -- FastAPI application entry point.

This module contains NO business logic. It only:
  1. Declares the FastAPI application (title/description/version).
  2. Registers the /health route.
  3. Includes the /procurement router (backend/api/routes/procurement.py).

The description is deliberately truthful about what this project is:
a rule-based, deterministic decision-support system built on Phase
2A/2B/5D/5E's own mathematical and graph-based algorithms -- NOT an
AI-powered or ML-forecasting product. Phase 5C's own closed research
finding (simple statistical baselines matched or outperformed the tested
ML model on the project's held-out Potato test period) remains the
project's conclusion and is not reopened or contradicted here.
"""

from fastapi import FastAPI

from backend.api.routes import procurement

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


@app.get("/health", summary="Health check")
def health() -> dict:
    """Confirms the API process is running. No database or external
    dependency exists in this project, so there is nothing further to
    check here."""
    return {"status": "ok"}


app.include_router(procurement.router)
