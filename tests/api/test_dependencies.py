"""
Phase 8B tests: repository selection in backend/api/dependencies.py.

Verifies the explicit, environment-variable-based switch between the
SQLite and Supabase repository implementations. No real Supabase
connection is made -- `SupabaseProcurementRunRepository.__init__` only
stores the connection string (confirmed directly in
tests/persistence/test_supabase_repository.py); constructing it here with
a fake URL performs no network I/O.

CRITICAL: confirms the default (DATABASE_URL unset, the real state of
this project's test/CI environment) resolves to SQLite -- this is what
keeps the entire automated test suite free of any real Supabase
dependency.
"""

from backend.api.dependencies import get_repository
from backend.persistence.sqlite_repository import SQLiteProcurementRunRepository
from backend.persistence.supabase_repository import SupabaseProcurementRunRepository


def test_default_repository_is_sqlite_when_database_url_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    repository = get_repository()
    assert isinstance(repository, SQLiteProcurementRunRepository)


def test_repository_is_supabase_when_database_url_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake-user:fake-password@fake-host:5432/fake-db")
    repository = get_repository()
    assert isinstance(repository, SupabaseProcurementRunRepository)


def test_repository_is_sqlite_when_database_url_is_empty_string(monkeypatch):
    # An empty string is falsy -- treated the same as "unset" rather than
    # attempting to connect to an empty connection string.
    monkeypatch.setenv("DATABASE_URL", "")
    repository = get_repository()
    assert isinstance(repository, SQLiteProcurementRunRepository)
