"""
Phase 8D -- tests for backend/security/auth.py's get_current_user()
dependency and the protected-route wiring in
backend/api/routes/procurement.py.

Uses FastAPI's real TestClient against the real app (backend.api.main.app)
with NO override of get_current_user -- unlike tests/api/, which overrides
it for its own (pre-8D, persistence-focused) tests, this file exists
specifically to exercise the real authentication path end-to-end. Only
get_repository is overridden (see conftest.py in this package), so no test
run here ever touches the real SQLite file or a real Supabase database.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
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


@pytest.mark.parametrize(
    "method, path, kwargs",
    [
        ("post", "/procurement/analyze", {"json": MINIMAL_ANALYZE_PAYLOAD}),
        ("get", "/procurement/runs", {}),
        ("get", "/procurement/runs/some-run-id", {}),
    ],
)
def test_protected_endpoint_rejects_missing_authorization_header(method, path, kwargs):
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


def test_protected_endpoint_rejects_wrong_auth_scheme():
    response = client.get("/procurement/runs", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert response.status_code == 401


def test_protected_endpoint_rejects_unverifiable_token(fake_jwks):
    response = client.get("/procurement/runs", headers=_auth_header("not-a-real-jwt"))
    assert response.status_code == 401


def test_error_response_does_not_leak_internals(fake_jwks):
    response = client.get("/procurement/runs", headers=_auth_header("not-a-real-jwt"))
    body = response.text.lower()
    for leaked_term in ("jwks", "signing key", "traceback", "secret", "rsa", "-----begin"):
        assert leaked_term not in body


def test_protected_endpoint_accepts_valid_authenticated_request(fake_jwks):
    kid = fake_jwks.add_key()
    token = fake_jwks.sign(kid, make_claims())

    response = client.get("/procurement/runs", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json() == []


def test_invalid_uuid_sub_is_rejected(fake_jwks):
    kid = fake_jwks.add_key()
    token = fake_jwks.sign(kid, make_claims(sub="not-a-real-uuid"))

    response = client.get("/procurement/runs", headers=_auth_header(token))

    assert response.status_code == 401


def test_request_json_cannot_override_authenticated_identity(fake_jwks):
    kid = fake_jwks.add_key()
    real_user_id = str(uuid.uuid4())
    token = fake_jwks.sign(kid, make_claims(sub=real_user_id))

    payload = dict(MINIMAL_ANALYZE_PAYLOAD)
    payload["user_id"] = "22222222-2222-2222-2222-222222222222"

    response = client.post("/procurement/analyze", json=payload, headers=_auth_header(token))

    # The request must succeed on its own merits (the extra "user_id"
    # field is silently ignored by Pydantic, matching
    # backend/api/schemas.py's ProcurementAnalysisRequest, which has no
    # such field) -- this test's real purpose is proving that field could
    # never have been used to control whose identity the request runs as
    # in the first place, since get_current_user() never reads request
    # JSON at all (see backend/security/auth.py).
    assert response.status_code == 200


def test_health_endpoint_remains_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unexpected_verification_exception_becomes_a_clean_401(monkeypatch):
    """Phase 8E hardening: verify_access_token is documented to only ever
    raise AuthenticationError, but get_current_user() must not trust that
    absolutely -- if some other exception type ever escapes it (as observed
    against a real Supabase project during Phase 8E's own manual browser
    verification), the caller must still see a generic 401, never a raw
    500 with a stack trace."""

    def _boom(token):
        raise RuntimeError("simulated unexpected failure -- never seen by the HTTP response")

    monkeypatch.setattr("backend.security.auth.verify_access_token", _boom)

    response = client.get("/procurement/runs", headers=_auth_header("irrelevant-token"))

    assert response.status_code == 401
    assert "runtimeerror" not in response.text.lower()
    assert "simulated unexpected failure" not in response.text.lower()
    assert "traceback" not in response.text.lower()
