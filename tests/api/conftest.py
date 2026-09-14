"""
Phase 6G -- test-only database isolation for every test under tests/api/.

Autouse so it applies uniformly to BOTH the new Phase 6G persistence-API
tests AND the pre-existing Phase 6F tests (tests/api/test_procurement_api.py)
-- POST /procurement/analyze now persists a run as a side effect, so
without this override those pre-existing tests would silently write to
the real data/app/procurement.db. Uses FastAPI's own
`app.dependency_overrides` mechanism (no new configuration framework) to
redirect backend.api.dependencies.get_repository to a pytest `tmp_path`
database for the duration of each test, then restores the override
mapping afterward.
"""

import pytest

from backend.api.dependencies import get_repository
from backend.api.main import app
from backend.persistence.repository import ProcurementRunRepository


@pytest.fixture(autouse=True)
def isolated_repository(tmp_path):
    test_repository = ProcurementRunRepository(tmp_path / "procurement_test.db")
    app.dependency_overrides[get_repository] = lambda: test_repository
    yield test_repository
    app.dependency_overrides.pop(get_repository, None)
