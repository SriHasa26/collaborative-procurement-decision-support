"""
Phase 6G -- test-only database isolation for every test under tests/api/.
Phase 8D -- test-only authentication bypass for the same tests.

Autouse so it applies uniformly to BOTH the new Phase 6G persistence-API
tests AND the pre-existing Phase 6F tests (tests/api/test_procurement_api.py)
-- POST /procurement/analyze now persists a run as a side effect, so
without this override those pre-existing tests would silently write to
the real data/app/procurement.db. Uses FastAPI's own
`app.dependency_overrides` mechanism (no new configuration framework) to
redirect backend.api.dependencies.get_repository to a pytest `tmp_path`
database for the duration of each test, then restores the override
mapping afterward.

Phase 8D added get_current_user (backend/security/auth.py) as a second
dependency on every route these tests call. These tests predate
authentication and are about persistence/business-logic behavior, not
authentication itself -- authentication's own behavior is exercised for
real, with no override, in tests/security/test_auth.py. Overriding
get_current_user here (the same dependency-override technique already
used for get_repository above, not a weakened assertion anywhere) keeps
every pre-existing test passing without needing a real or fabricated JWT.
"""

import pytest

from backend.api.dependencies import get_repository
from backend.api.main import app
from backend.persistence.sqlite_repository import SQLiteProcurementRunRepository
from backend.security.auth import AuthenticatedUser, get_current_user

# Public (not underscore-prefixed) so other tests/api/ test modules that
# call the isolated repository directly (e.g.
# tests/api/test_procurement_runs_api.py) can pass the SAME user_id the
# route itself used via bypass_authentication below -- Phase 8F's
# ownership filtering means a test asserting on stored rows must query
# with the identity that owns them.
FAKE_TEST_USER = AuthenticatedUser(user_id="00000000-0000-0000-0000-000000000000", email="test@example.com")


@pytest.fixture(autouse=True)
def isolated_repository(tmp_path):
    test_repository = SQLiteProcurementRunRepository(tmp_path / "procurement_test.db")
    app.dependency_overrides[get_repository] = lambda: test_repository
    yield test_repository
    app.dependency_overrides.pop(get_repository, None)


@pytest.fixture(autouse=True)
def bypass_authentication():
    app.dependency_overrides[get_current_user] = lambda: FAKE_TEST_USER
    yield FAKE_TEST_USER
    app.dependency_overrides.pop(get_current_user, None)
