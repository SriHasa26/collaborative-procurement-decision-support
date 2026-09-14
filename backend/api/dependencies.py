"""
Phase 6G -- FastAPI dependency wiring for the persistence repository.

ONE function, get_repository(), is the seam tests use to redirect
persistence to a temporary database via FastAPI's own
`app.dependency_overrides` mechanism (see tests/api/test_procurement_runs_api.py)
-- no separate configuration framework is introduced, and the production
default database path is never hard-coded into a route handler.
"""

from backend.persistence.database import DEFAULT_DB_PATH
from backend.persistence.repository import ProcurementRunRepository


def get_repository() -> ProcurementRunRepository:
    return ProcurementRunRepository(DEFAULT_DB_PATH)
