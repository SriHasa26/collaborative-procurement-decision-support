"""
Phase 8D -- tests for backend/security/jwt_verifier.py: genuine
cryptographic JWT verification, JWKS caching, and key rotation.

Every token here is signed locally with a keypair generated in this test
run (tests/security/conftest.py); the same real jwt_verifier.verify_access_token
code path that production uses is exercised throughout -- nothing about
verification itself is weakened or bypassed for these tests, only the
network JWKS fetch is faked (see conftest.py's fake_jwks fixture).
"""

import json

import jwt as pyjwt
import pytest
from jwt.utils import base64url_encode

from backend.security.jwt_verifier import AuthenticationError, verify_access_token
from tests.security.conftest import TEST_AUDIENCE, TEST_ISSUER, make_claims


def test_valid_token_is_verified_and_claims_returned(fake_jwks):
    kid = fake_jwks.add_key()
    claims = make_claims()
    token = fake_jwks.sign(kid, claims)

    verified = verify_access_token(token)

    assert verified["sub"] == claims["sub"]
    assert verified["aud"] == TEST_AUDIENCE
    assert verified["iss"] == TEST_ISSUER


def test_malformed_token_is_rejected(fake_jwks):
    with pytest.raises(AuthenticationError):
        verify_access_token("this-is-not-a-jwt")


def test_expired_token_is_rejected(fake_jwks):
    kid = fake_jwks.add_key()
    token = fake_jwks.sign(kid, make_claims(exp_delta=-3600))

    with pytest.raises(AuthenticationError):
        verify_access_token(token)


def test_invalid_signature_is_rejected(fake_jwks):
    # kid "k1" is published with genuine_key's PUBLIC half, but the token
    # is actually signed with a different, unrelated private key -- a
    # forged token an attacker without the real private key could not
    # otherwise produce.
    genuine_kid = fake_jwks.add_key(kid="k1")
    forged_key = fake_jwks.add_key(kid="k2")
    forged_token = pyjwt.encode(
        make_claims(),
        # Sign with k2's private key, but claim k1's kid in the header, so
        # PyJWKClient resolves the *wrong* (k1's) public key for it.
        fake_jwks._private_keys_by_kid[forged_key],
        algorithm="RS256",
        headers={"kid": genuine_kid},
    )

    with pytest.raises(AuthenticationError):
        verify_access_token(forged_token)


def test_incorrect_issuer_is_rejected(fake_jwks):
    kid = fake_jwks.add_key()
    token = fake_jwks.sign(kid, make_claims(iss="https://attacker-project.supabase.co/auth/v1"))

    with pytest.raises(AuthenticationError):
        verify_access_token(token)


def test_incorrect_audience_is_rejected(fake_jwks):
    kid = fake_jwks.add_key()
    token = fake_jwks.sign(kid, make_claims(aud="not-authenticated"))

    with pytest.raises(AuthenticationError):
        verify_access_token(token)


def test_missing_sub_claim_is_rejected(fake_jwks):
    kid = fake_jwks.add_key()
    claims = make_claims()
    del claims["sub"]
    token = fake_jwks.sign(kid, claims)

    with pytest.raises(AuthenticationError):
        verify_access_token(token)


def test_alg_none_is_never_accepted(fake_jwks):
    fake_jwks.add_key()
    # A token that declares alg "none" and carries no signature at all --
    # the classic JWT forgery. Must be rejected outright, never accepted
    # by "trusting" whatever algorithm the token itself names.
    header = base64url_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode()
    payload = base64url_encode(json.dumps(make_claims()).encode()).decode()
    forged = f"{header}.{payload}."

    with pytest.raises(AuthenticationError):
        verify_access_token(forged)


def test_unknown_kid_triggers_exactly_one_controlled_refresh_then_succeeds(fake_jwks):
    priming_kid = fake_jwks.add_key()
    priming_token = fake_jwks.sign(priming_kid, make_claims())
    verify_access_token(priming_token)  # primes the JWKS cache
    assert fake_jwks.fetch_count == 1

    # A key that did not exist at priming time -- simulates a genuinely
    # unknown kid that only a refresh can discover.
    new_kid = fake_jwks.add_key()
    new_token = fake_jwks.sign(new_kid, make_claims())

    verified = verify_access_token(new_token)

    assert verified["sub"] is not None
    # Exactly one additional fetch (the controlled refresh) -- not zero
    # (it must have refreshed to find the new key) and not more than one
    # (no refresh loop).
    assert fake_jwks.fetch_count == 2


def test_unknown_kid_that_still_does_not_exist_fails_cleanly_without_looping(fake_jwks):
    priming_kid = fake_jwks.add_key()
    verify_access_token(fake_jwks.sign(priming_kid, make_claims()))
    assert fake_jwks.fetch_count == 1

    # Signed with a real key, but under a kid never published at all --
    # a genuinely unknown kid, never discoverable by any refresh.
    phantom_key = fake_jwks.add_key()
    phantom_token = fake_jwks.sign(phantom_key, make_claims())
    fake_jwks.remove_key(phantom_key)

    with pytest.raises(AuthenticationError):
        verify_access_token(phantom_token)

    # One controlled refresh happened (fetch_count went from 1 to 2), and
    # no more -- a broken/looping implementation would keep refreshing.
    assert fake_jwks.fetch_count == 2


def test_key_rotation_new_key_validates_after_refresh(fake_jwks):
    old_kid = fake_jwks.add_key()
    old_token = fake_jwks.sign(old_kid, make_claims())
    verify_access_token(old_token)

    # Rotate: publish a new key and retire the old one, exactly as a real
    # Supabase project's key rotation would.
    new_kid = fake_jwks.add_key()
    fake_jwks.remove_key(old_kid)
    new_token = fake_jwks.sign(new_kid, make_claims())

    verified = verify_access_token(new_token)

    assert verified["sub"] is not None


def test_jwks_is_not_fetched_on_every_call_once_cached(fake_jwks):
    kid = fake_jwks.add_key()
    token = fake_jwks.sign(kid, make_claims())

    verify_access_token(token)
    fetch_count_after_first_call = fake_jwks.fetch_count

    verify_access_token(token)
    verify_access_token(token)

    assert fake_jwks.fetch_count == fetch_count_after_first_call


def test_supabase_url_not_configured_is_rejected(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)

    with pytest.raises(AuthenticationError):
        verify_access_token("irrelevant-token-value")
