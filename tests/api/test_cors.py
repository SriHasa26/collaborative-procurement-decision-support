"""
Phase 8E -- confirms the CORS preflight response allows the `Authorization`
header, added to backend/api/main.py's `allow_headers` alongside this
phase's frontend change (frontend/src/api/client.js now sends
`Authorization: Bearer <token>`). Without this, a real browser's preflight
`OPTIONS` request would reject the header before FastAPI ever saw the
actual request -- this test would have failed before Phase 8E's fix and
is the regression guard for it.

Starlette's CORSMiddleware answers a matching preflight OPTIONS request
directly (before any route/dependency runs), so this needs no
authentication fixture and does not exercise get_current_user() at all.
"""

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_cors_preflight_allows_authorization_header():
    response = client.options(
        "/procurement/runs",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allowed_headers


def test_cors_preflight_still_allows_content_type_header():
    response = client.options(
        "/procurement/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in allowed_headers
