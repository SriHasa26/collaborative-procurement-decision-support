"""
Phase 8D -- FastAPI-facing authentication layer.

Exposes get_current_user(), a FastAPI dependency that protected routes add
alongside their existing `repository: ProcurementRunRepository =
Depends(get_repository)` parameter (backend/api/dependencies.py is not
modified by this phase -- see that module's own docstring). The verified
user identity comes ONLY from here -- never from request JSON (see
backend/api/schemas.py: no request model in this project has ever had a
user_id field, and this phase does not add one).

This module contains no JWT/JWKS logic of its own; it only calls
backend.security.jwt_verifier.verify_access_token and translates the
result (or any failure) into FastAPI terms. This keeps the pure
verification logic in jwt_verifier.py independently testable without any
FastAPI/HTTP concept, matching this project's existing layering
(backend/core/ has no HTTP concept either).
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.security.jwt_verifier import AuthenticationError, verify_access_token

# auto_error=True (the default) makes FastAPI itself raise HTTP 401 with a
# generic "Not authenticated" detail when the Authorization header is
# missing entirely, or does not use the "Bearer" scheme -- confirmed by
# inspecting the installed fastapi package's HTTPBearer.__call__ /
# make_not_authenticated_error source, which already uses 401 (not FastAPI's
# older HTTPBasic-style 403) and never echoes back header contents. Reused
# here rather than hand-rolling identical header-parsing logic.
_bearer_scheme = HTTPBearer(auto_error=True)

# The single generic message returned for every authentication failure this
# module produces, regardless of cause (expired, bad signature, wrong
# issuer/audience, malformed, unresolvable key, invalid subject). Never
# includes the underlying jwt/PyJWKClient exception message, a key, a JWKS
# URL, or any other internal detail -- see reports/phase8d_fastapi_jwt_authentication.md
# Section "Security audit".
_INVALID_TOKEN_DETAIL = "Invalid authentication token"


@dataclass(frozen=True)
class AuthenticatedUser:
    """The minimal verified identity of the caller of a protected route.

    Deliberately NOT a full user/profile domain model -- it carries only
    what a verified access token actually proves: a real Supabase user id
    (validated as a UUID) and, if present in the token, an email. Nothing
    here is read from, or ever merged with, request JSON."""

    user_id: str
    email: Optional[str] = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    """FastAPI dependency: verifies the request's bearer token and returns
    the caller's verified identity, or raises HTTP 401.

    The token's `sub` claim is the ONLY source of user_id -- request JSON
    is never consulted (and no request schema in this project has a
    user_id field to consult in the first place). `sub` must be a
    syntactically valid UUID; Supabase always issues one for a real user,
    so a missing/non-UUID `sub` indicates a token this application does
    not trust and is rejected the same as any other verification failure.
    """
    try:
        claims = verify_access_token(credentials.credentials)
    except AuthenticationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_TOKEN_DETAIL)
    except Exception:
        # Phase 8E hardening: verify_access_token is documented to raise
        # only AuthenticationError, but a real access token against a real,
        # live Supabase project exercises code paths (network timing, JWKS
        # response shape, claim shapes an offline test token can't
        # replicate exactly) a test suite cannot fully replicate. Letting
        # anything else escape as an unhandled exception would produce a
        # raw HTTP 500 -- possibly with a traceback -- for what is still,
        # from the caller's perspective, an authentication failure. This is
        # the same generic 401 as every other verification failure; it
        # never re-raises or logs the original exception to the response
        # (see this module's docstring and Step 8/9 of
        # reports/phase8e_supabase_fastapi_integration.md).
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_TOKEN_DETAIL)

    subject = claims.get("sub")
    try:
        user_id = str(UUID(str(subject)))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_TOKEN_DETAIL)

    email = claims.get("email")
    if not isinstance(email, str):
        email = None

    return AuthenticatedUser(user_id=user_id, email=email)
