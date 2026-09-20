"""
Phase 8D -- shared fixtures for tests/security/.

Everything here is entirely local and offline: a locally-generated RSA
keypair per test key, a fake in-memory JWKS "server" object, and a
monkeypatch of jwt.PyJWKClient.fetch_data (the exact method that performs
PyJWKClient's own network fetch -- confirmed by reading its source, see
backend/security/jwt_verifier.py's own docstring) so PyJWKClient's real,
unmodified caching/refresh/parsing logic runs against this fake data
instead of the network. No real Supabase project, account, credential, or
internet access is used anywhere in this test package -- the closest thing
to a "project URL" here is TEST_SUPABASE_URL below, a placeholder that is
never actually contacted.
"""

import io
import json
import time
import urllib.request
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from backend.api.dependencies import get_repository
from backend.api.main import app
from backend.persistence.sqlite_repository import SQLiteProcurementRunRepository
from backend.security import jwt_verifier

TEST_SUPABASE_URL = "https://test-project.supabase.co"
TEST_ISSUER = f"{TEST_SUPABASE_URL}/auth/v1"
TEST_AUDIENCE = "authenticated"


def _generate_rsa_keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _public_jwk(private_key, kid):
    jwk = RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    jwk["kid"] = kid
    jwk["alg"] = "RS256"
    jwk["use"] = "sig"
    return jwk


class FakeJwksServer:
    """In-memory stand-in for a Supabase project's JWKS endpoint.

    Tests add/remove keys directly (add_key/remove_key) to simulate normal
    operation and key rotation; fetch_count lets a test assert the real
    verification code path did NOT fetch on every call (only on a cache
    miss/refresh)."""

    def __init__(self):
        self._private_keys_by_kid = {}
        self.fetch_count = 0

    def add_key(self, kid=None):
        kid = kid or str(uuid.uuid4())
        self._private_keys_by_kid[kid] = _generate_rsa_keypair()
        return kid

    def remove_key(self, kid):
        del self._private_keys_by_kid[kid]

    def sign(self, kid, claims, headers=None):
        private_key = self._private_keys_by_kid[kid]
        token_headers = {"kid": kid}
        if headers:
            token_headers.update(headers)
        return jwt.encode(claims, private_key, algorithm="RS256", headers=token_headers)

    def as_jwks_response(self):
        self.fetch_count += 1
        return {
            "keys": [_public_jwk(key, kid) for kid, key in self._private_keys_by_kid.items()]
        }


class _FakeHttpResponse(io.BytesIO):
    """Minimal stand-in for the object urllib.request.urlopen() returns:
    supports the `with urlopen(...) as response:` context-manager usage
    and json.load(response)'s `.read()` calls, nothing else."""

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
        return False


@pytest.fixture
def fake_jwks(monkeypatch):
    server = FakeJwksServer()

    def fake_urlopen(request, timeout=None, context=None):
        # This is the ONLY thing faked: the actual network round trip.
        # jwt.PyJWKClient.fetch_data / get_jwk_set / get_signing_key /
        # JWKSetCache are all the real, unmodified library code, so the
        # cache-on-success behavior their real fetch_data implements in
        # its own `finally` block still genuinely runs.
        body = json.dumps(server.as_jwks_response()).encode("utf-8")
        return _FakeHttpResponse(body)

    # The exact external boundary PyJWKClient.fetch_data itself calls
    # (confirmed by reading its source: `urllib.request.urlopen(...)`) --
    # monkeypatched here rather than anything in this project's own code,
    # so PyJWKClient's real fetch/cache/refresh logic is genuinely
    # exercised end-to-end against this fake transport.
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("SUPABASE_URL", TEST_SUPABASE_URL)
    monkeypatch.delenv("SUPABASE_JWT_AUDIENCE", raising=False)
    jwt_verifier.reset_jwk_client_cache()
    yield server
    jwt_verifier.reset_jwk_client_cache()


@pytest.fixture(autouse=True)
def isolated_repository(tmp_path):
    """Same isolation technique as tests/api/conftest.py's fixture of the
    same name: redirects get_repository to a tmp_path SQLite file so
    tests/security/test_auth.py's real requests through
    backend/api/routes/procurement.py never touch the real
    data/app/procurement.db. Deliberately does NOT override
    get_current_user -- this package exists specifically to exercise the
    real authentication dependency."""
    test_repository = SQLiteProcurementRunRepository(tmp_path / "procurement_test.db")
    app.dependency_overrides[get_repository] = lambda: test_repository
    yield test_repository
    app.dependency_overrides.pop(get_repository, None)


def make_claims(sub=None, aud=TEST_AUDIENCE, iss=TEST_ISSUER, exp_delta=3600, **extra):
    now = int(time.time())
    claims = {
        "sub": sub if sub is not None else str(uuid.uuid4()),
        "aud": aud,
        "iss": iss,
        "iat": now,
        "exp": now + exp_delta,
        "email": "vendor@example.com",
    }
    claims.update(extra)
    return claims
