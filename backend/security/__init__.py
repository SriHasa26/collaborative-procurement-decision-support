"""Phase 8D -- authentication/identity-verification package.

Deliberately separate from backend/api/ (HTTP routing/schemas) and
backend/core/ (the decision engine, which must never contain auth logic --
see reports/phase8d_fastapi_jwt_authentication.md). Mirrors this project's
existing convention of one top-level package per concern (backend/core/,
backend/persistence/, backend/services/).

backend/security/jwt_verifier.py -- pure JWT/JWKS verification (no FastAPI
    import, no HTTP concepts). Returns raw verified claims or raises
    AuthenticationError.
backend/security/auth.py -- the FastAPI-facing layer: the AuthenticatedUser
    model, the get_current_user() dependency, and the mapping from any
    verification failure to a generic HTTP 401.
"""
