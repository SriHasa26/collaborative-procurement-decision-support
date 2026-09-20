"""
Phase 8D -- local (JWKS-based) cryptographic verification of Supabase-issued
access tokens.

ARCHITECTURE (see reports/phase8a_supabase_multiuser_architecture.md
Section 14 and this phase's own report, Section "Architectural ambiguity
resolved"): Supabase's current default for new projects signs access
tokens asymmetrically (RS256 or ES256) and publishes the corresponding
public verification keys at a per-project JWKS endpoint. This module
fetches that JWKS, verifies each token's signature locally against it, and
never makes a network call to Supabase's own /auth/v1/user endpoint (which
would defeat local verification and cost a round trip per request -- see
Phase 8D prompt Section 5). This is a documented assumption (JWKS/
asymmetric over the legacy shared-secret/HS256 mechanism some older
Supabase projects use) made because the task's own instructions describe
only the JWKS architecture and never mention a shared secret; it is not
independently confirmed against the user's live project, since doing so
would require making a live call with real project credentials, which this
phase's own constraints forbid. If the user's project turns out to still
use the legacy HS256 mechanism, this module's SUPABASE_URL-derived JWKS
fetch will simply fail closed (every token rejected, never silently
accepted) -- see verify_access_token's error handling below.

WHY NOT jwt.decode()'s own algorithm-from-token behavior: this module never
lets the token's own `alg` header choose the verification algorithm.
ALLOWED_ALGORITHMS below is a fixed allow-list passed explicitly to
jwt.decode(); PyJWT rejects any token whose header names an algorithm
outside that list (including "none") before attempting verification.

CACHING (Phase 8D Section 12-13's requirement -- no per-request JWKS
fetch, a bounded simple in-process cache, and "unknown kid -> one
controlled refresh -> clean failure", not an infinite loop): rather than
hand-rolling this, this module reuses jwt.PyJWKClient directly (confirmed
by source inspection to already implement exactly this: a bounded
JWKSetCache with a 300-second default lifespan, and get_signing_key()'s
existing "look up kid -> on miss, refresh the set exactly once -> look up
again -> raise cleanly if still missing" logic). _get_jwk_client() below
is wrapped in functools.lru_cache(maxsize=1) purely so that the *same*
PyJWKClient instance (and therefore the same JWKSetCache) is reused across
requests within one process -- constructing a fresh PyJWKClient per
request would reset its cache every time and reintroduce the per-request
fetch this requirement forbids.
"""

import os
from functools import lru_cache

import jwt
from jwt import PyJWKClient

# Supabase's modern (JWKS-based) projects sign access tokens with an
# asymmetric algorithm. Both RS256 and ES256 are allow-listed since Supabase
# has used each depending on project age/configuration; neither HS256 nor
# any other algorithm is accepted, and this list is never derived from the
# token itself.
ALLOWED_ALGORITHMS = ["RS256", "ES256"]

# Supabase's own default audience claim for authenticated-user access
# tokens. Overridable via SUPABASE_JWT_AUDIENCE for a project configured
# differently, but defaults to the value every standard Supabase project
# issues, so no project-specific setup is required beyond SUPABASE_URL.
DEFAULT_AUDIENCE = "authenticated"


class AuthenticationError(Exception):
    """Raised for any failure to verify an access token.

    Deliberately carries no structured detail beyond a short message
    intended for internal logs/debugging -- backend/security/auth.py never
    forwards this exception's message to an API response. See this
    module's own docstring and reports/phase8d_fastapi_jwt_authentication.md
    Section "Security audit" (auth errors don't leak secrets)."""


def _jwks_url(supabase_url: str) -> str:
    return f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


def _issuer(supabase_url: str) -> str:
    return f"{supabase_url.rstrip('/')}/auth/v1"


@lru_cache(maxsize=1)
def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    """Bounded (maxsize=1 -- this process only ever talks to one Supabase
    project) in-process cache of the PyJWKClient instance itself, so its
    internal JWKS cache survives across requests. Tests must clear this via
    reset_jwk_client_cache() before/after monkeypatching SUPABASE_URL or the
    JWKS fetch, since a stale cached client would otherwise silently ignore
    a test's new configuration."""
    return PyJWKClient(jwks_url)


def reset_jwk_client_cache() -> None:
    """Test-only escape hatch: clears the cached PyJWKClient (and, with it,
    its internal JWKS cache) so each test starts from a clean state. Not
    called anywhere in production code -- there is no reason to evict this
    cache during normal operation."""
    _get_jwk_client.cache_clear()


def verify_access_token(token: str) -> dict:
    """Cryptographically verifies `token` against the configured Supabase
    project's published JWKS and returns its decoded claims.

    Verifies, via PyJWT: signature (against the JWKS-resolved public key),
    algorithm (restricted to ALLOWED_ALGORITHMS -- never "none", never
    whatever the token itself declares), issuer, audience, expiration, and
    that `exp`/`sub`/`iss`/`aud` are all present. Raises AuthenticationError
    -- never a raw PyJWT exception, never the underlying key/JWKS details
    -- for every failure mode: missing configuration, an unresolvable
    `kid`, a bad signature, an expired token, a wrong issuer/audience, or
    a malformed token. Callers (backend/security/auth.py) are responsible
    for turning this into an HTTP 401; this function has no HTTP concept
    of its own."""
    supabase_url = os.environ.get("SUPABASE_URL")
    if not supabase_url:
        raise AuthenticationError("SUPABASE_URL is not configured")

    jwk_client = _get_jwk_client(_jwks_url(supabase_url))

    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
    except jwt.exceptions.PyJWTError as exc:
        raise AuthenticationError("unable to resolve a signing key for this token") from exc

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            audience=os.environ.get("SUPABASE_JWT_AUDIENCE", DEFAULT_AUDIENCE),
            issuer=_issuer(supabase_url),
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
    except jwt.exceptions.PyJWTError as exc:
        raise AuthenticationError("token failed verification") from exc

    return claims
