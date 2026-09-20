"""
Phase 6G tests: the HTTP persistence endpoints
(POST /procurement/analyze's persistence side effect, GET /procurement/runs,
GET /procurement/runs/{run_id}).

Covers required test cases T7-T10 (numbering per the Phase 6G task spec).
Every test goes through the real HTTP layer via FastAPI's TestClient --
none manually invokes the repository or ProcurementRunService directly
(except to independently confirm what was persisted, via the
`isolated_repository` fixture object itself -- the very same repository
instance the route used, per tests/api/conftest.py's dependency override).

The `isolated_repository` fixture (tests/api/conftest.py, autouse) points
every test at a pytest `tmp_path` database -- the real
data/app/procurement.db is never touched by these tests.
"""

from fastapi.testclient import TestClient

from backend.api.main import app
from tests.api.conftest import FAKE_TEST_USER
from tests.fixtures.api_fixtures import (
    ABSTAIN_NO_EVIDENCE,
    ELIGIBLE_1,
    ELIGIBLE_2,
    ELIGIBLE_3,
    VALIDATION_ERROR_NEGATIVE_QTY,
    build_request_payload,
)

client = TestClient(app)


# --- T7: API persistence ---
def test_t7_analyze_persists_a_run(isolated_repository):
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])

    response = client.post("/procurement/analyze", json=payload)

    assert response.status_code == 200
    stored = isolated_repository.list_runs(FAKE_TEST_USER.user_id)
    assert len(stored) == 1
    assert stored[0].commodity == "tomato"
    assert stored[0].run_status == response.json()["run_status"]


def test_analyze_response_is_unchanged_by_persistence(isolated_repository):
    """The response body must be exactly the Phase 6F analysis result --
    persistence is a side effect, never a reshaping of the returned data."""
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3])
    response = client.post("/procurement/analyze", json=payload)
    body = response.json()

    assert "run_id" not in body  # persistence metadata does not leak into the analysis response
    assert body["run_status"] == "COMPLETED"
    assert body["final_selection"]["selected_group_ids"]


# --- T8: API run history ---
def test_t8_run_history_lists_saved_runs(isolated_repository):
    client.post("/procurement/analyze", json=build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3]))
    client.post("/procurement/analyze", json=build_request_payload([ELIGIBLE_1, ELIGIBLE_2]))

    response = client.get("/procurement/runs")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    for entry in body:
        assert set(entry.keys()) == {"run_id", "created_at", "commodity", "run_status"}
        assert entry["commodity"] == "tomato"


def test_run_history_reflects_mixed_outcomes(isolated_repository):
    client.post(
        "/procurement/analyze",
        json=build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3, ABSTAIN_NO_EVIDENCE, VALIDATION_ERROR_NEGATIVE_QTY]),
    )

    body = client.get("/procurement/runs").json()
    assert len(body) == 1
    assert body[0]["run_status"] == "COMPLETED_WITH_ABSTENTIONS"


# --- T9: API single run ---
def test_t9_get_single_run(isolated_repository):
    client.post("/procurement/analyze", json=build_request_payload([ELIGIBLE_1, ELIGIBLE_2, ELIGIBLE_3]))
    run_id = client.get("/procurement/runs").json()[0]["run_id"]

    response = client.get(f"/procurement/runs/{run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["commodity"] == "tomato"
    assert body["run_status"] == "COMPLETED"
    assert body["input"]["commodity"]["commodity_id"] == "tomato"
    assert body["result"]["final_selection"]["selected_group_ids"]
    assert len(body["result"]["final_selection"]["all_evaluated_results"]) > 0


# --- T10: API unknown run ---
def test_t10_get_unknown_run_returns_404(isolated_repository):
    response = client.get("/procurement/runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    # No raw SQLite error text, no stack trace, no internal path leaked.
    assert "sqlite3" not in str(body).lower()
    assert "traceback" not in str(body).lower()


# --- Existing Phase 6F behavior must be unchanged by this phase ---
def test_malformed_analyze_request_still_returns_422(isolated_repository):
    payload = build_request_payload([ELIGIBLE_1, ELIGIBLE_2])
    del payload["commodity"]
    response = client.post("/procurement/analyze", json=payload)
    assert response.status_code == 422
    # A malformed/rejected request must never be persisted.
    assert isolated_repository.list_runs(FAKE_TEST_USER.user_id) == []
