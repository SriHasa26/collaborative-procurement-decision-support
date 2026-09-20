"""
Phase 6G -- FastAPI dependency wiring for the persistence repository.
Phase 8B -- selects between the SQLite and Supabase implementations
explicitly, based on whether the `DATABASE_URL` environment variable is
set (reports/phase8a_supabase_multiuser_architecture.md Section 14 names
this exact variable for a direct Postgres connection string).

ONE function, get_repository(), is the seam tests use to redirect
persistence to a temporary database via FastAPI's own
`app.dependency_overrides` mechanism (see tests/api/conftest.py) -- no
separate configuration framework is introduced, and neither the
production SQLite path nor a real database connection string is ever
hard-coded into a route handler.

DEFAULT BEHAVIOR, load-bearing for the test suite: `DATABASE_URL` is unset
in the test/CI environment (nothing in this project sets it), so
`get_repository()` -- and therefore every test that does not explicitly
override it -- resolves to SQLiteProcurementRunRepository. The automated
test suite never requires real Supabase credentials, never contacts a
real cloud database, and never needs internet access as a result of this
function's own logic (Phase 8B Step "No real cloud data during tests").
"""

import os

from backend.persistence.database import DEFAULT_DB_PATH
from backend.persistence.repository import ProcurementRunRepository
from backend.persistence.sqlite_repository import SQLiteProcurementRunRepository
from backend.persistence.supabase_repository import SupabaseProcurementRunRepository


def get_repository() -> ProcurementRunRepository:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return SupabaseProcurementRunRepository(database_url)
    return SQLiteProcurementRunRepository(DEFAULT_DB_PATH)
