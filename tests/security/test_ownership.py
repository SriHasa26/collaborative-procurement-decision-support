"""
Phase 8F -- cross-user ownership tests, exercised through the real HTTP
layer (backend/api/routes/procurement.py) with real, distinct verified
identities for two different users. Reuses tests/security/conftest.py's
`fake_jwks` and `isolated_repository` fixtures (the same offline JWT/JWKS
and SQLite-isolation infrastructure Phase 8D already built) rather than
building a second, parallel test system -- per this phase's own "avoid
duplicating JWT generation/JWKS mocking" instruction.

Every test in this file uses TWO distinct, locally-signed JWTs (one per
simulated user) against the SAME running app/repository, and asserts one
user's actions are never visible to, or triggerable by, the other. No
real Supabase user, credential, or network access is used anywhere here.

Test numbering below (T1-T11) matches the Phase 8F task spec's own
required test list; T12 (missing auth -> 401) and T13 (GET /health public)
are already covered by tests/security/test_auth.py and are not duplicated
here (Section 21: reuse existing coverage rather than re-testing the same
behavior under a second name).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.persistence.database import get_connection
from tests.security.conftest import make_claims

client = TestClient(app)

MINIMAL_ANALYZE_PAYLOAD = {
    "commodity": {"commodity_id": "potato"},
    "context": {"commodity_id": "potato", "date": "2026-01-01"},
    "vendor_submissions": [],
    "config": {"d_max_km": 5.0, "trader_margin": 0.1, "transport_tiers": []},
}


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def two_users(fake_jwks):
    """Two distinct, real (locally-signed) identities against the same
    fake JWKS -- USER_A and USER_B are never the same UUID."""
    kid = fake_jwks.add_key()
    user_a_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())
    token_a = fake_jwks.sign(kid, make_claims(sub=user_a_id))
    token_b = fake_jwks.sign(kid, make_claims(sub=user_b_id))
    return {
        "a_id": user_a_id,
        "b_id": user_b_id,
        "a_header": _auth_header(token_a),
        "b_header": _auth_header(token_b),
    }


def _save_run(headers):
    response = client.post("/procurement/analyze", json=MINIMAL_ANALYZE_PAYLOAD, headers=headers)
    assert response.status_code == 200
    run_id = client.get("/procurement/runs", headers=headers).json()[0]["run_id"]
    return run_id


# --- T1/T2: save_run records the correct verified owner ---
def test_t1_user_a_run_is_stored_under_user_a(two_users, isolated_repository):
    _save_run(two_users["a_header"])

    stored = isolated_repository.list_runs(two_users["a_id"])
    assert len(stored) == 1


def test_t2_user_b_run_is_stored_under_user_b(two_users, isolated_repository):
    _save_run(two_users["b_header"])

    stored = isolated_repository.list_runs(two_users["b_id"])
    assert len(stored) == 1


# --- T3/T4: list_runs is scoped per user ---
def test_t3_user_a_list_shows_only_user_a_runs(two_users):
    _save_run(two_users["a_header"])
    _save_run(two_users["b_header"])

    response = client.get("/procurement/runs", headers=two_users["a_header"])
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_t4_user_b_list_shows_only_user_b_runs(two_users):
    _save_run(two_users["a_header"])
    _save_run(two_users["b_header"])

    response = client.get("/procurement/runs", headers=two_users["b_header"])
    assert response.status_code == 200
    assert len(response.json()) == 1


# --- T5/T6: each user can retrieve their own run ---
def test_t5_user_a_can_retrieve_own_run(two_users):
    run_id = _save_run(two_users["a_header"])

    response = client.get(f"/procurement/runs/{run_id}", headers=two_users["a_header"])
    assert response.status_code == 200
    assert response.json()["run_id"] == run_id


def test_t6_user_b_can_retrieve_own_run(two_users):
    run_id = _save_run(two_users["b_header"])

    response = client.get(f"/procurement/runs/{run_id}", headers=two_users["b_header"])
    assert response.status_code == 200
    assert response.json()["run_id"] == run_id


# --- T7/T8: cross-user retrieval is denied as 404, never 403 ---
def test_t7_user_a_cannot_retrieve_user_b_run(two_users):
    run_id_b = _save_run(two_users["b_header"])

    response = client.get(f"/procurement/runs/{run_id_b}", headers=two_users["a_header"])
    assert response.status_code == 404


def test_t8_user_b_cannot_retrieve_user_a_run(two_users):
    run_id_a = _save_run(two_users["a_header"])

    response = client.get(f"/procurement/runs/{run_id_a}", headers=two_users["b_header"])
    assert response.status_code == 404


# --- T9: unknown run id ---
def test_t9_unknown_run_id_returns_404(two_users):
    response = client.get(
        "/procurement/runs/00000000-0000-0000-0000-000000000000", headers=two_users["a_header"]
    )
    assert response.status_code == 404


# --- T10: legacy NULL-owner row is invisible to any authenticated user ---
def test_t10_legacy_null_owner_row_is_not_exposed(two_users, isolated_repository, tmp_path):
    # Insert a legacy row directly (bypassing save_run) with NULL user_id,
    # simulating a run persisted before Phase 8F/authentication existed.
    # `tmp_path` here resolves to the SAME path isolated_repository
    # (tests/security/conftest.py) already constructed its repository
    # against, since both fixtures receive the identical per-test tmp_path.
    conn = get_connection(tmp_path / "procurement_test.db")
    try:
        conn.execute(
            "INSERT INTO procurement_runs "
            "(run_id, user_id, created_at, commodity, run_status, eligible_vendor_count, "
            "candidate_group_count, selected_group_count, input_json, result_json) "
            "VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("legacy-run-id", "2026-01-01T00:00:00+00:00", "potato", "COMPLETED", 0, 0, 0, "{}", "{}"),
        )
        conn.commit()
    finally:
        conn.close()

    get_response = client.get("/procurement/runs/legacy-run-id", headers=two_users["a_header"])
    assert get_response.status_code == 404

    list_response = client.get("/procurement/runs", headers=two_users["b_header"])
    assert "legacy-run-id" not in {row["run_id"] for row in list_response.json()}


# --- T11: request JSON cannot assign a run to a different user ---
def test_t11_spoofed_user_id_in_request_body_does_not_change_ownership(two_users):
    payload = dict(MINIMAL_ANALYZE_PAYLOAD)
    payload["user_id"] = two_users["b_id"]  # User A attempts to claim to be User B

    response = client.post("/procurement/analyze", json=payload, headers=two_users["a_header"])
    assert response.status_code == 200

    # The run belongs to User A (the verified token holder) -- User B's
    # list must NOT show it, and User A's list must.
    assert len(client.get("/procurement/runs", headers=two_users["b_header"]).json()) == 0
    assert len(client.get("/procurement/runs", headers=two_users["a_header"]).json()) == 1
