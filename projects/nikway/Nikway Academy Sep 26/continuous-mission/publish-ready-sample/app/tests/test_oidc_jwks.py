from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

pytest.importorskip("jwt")
import jwt

import app.auth as auth


def _token(**overrides):
    claims = {
        "iss": "https://issuer.example",
        "aud": "nikway-api",
        "sub": "user-1",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(claims, "test-secret", algorithm="HS256")


def test_jwks_verifier_uses_resolved_signing_key(monkeypatch):
    class FakeClient:
        def __init__(self, url):
            assert url == "https://issuer.example/jwks"

        def get_signing_key_from_jwt(self, token):
            assert token
            return SimpleNamespace(key="test-secret")

    monkeypatch.setattr(auth, "PyJWKClient", FakeClient)
    claims = auth.verify_oidc_token_from_jwks(
        _token(),
        jwks_url="https://issuer.example/jwks",
        issuer="https://issuer.example",
        audience="nikway-api",
        algorithms=["HS256"],
    )
    assert claims["sub"] == "user-1"


def test_jwks_verifier_rejects_invalid_provider_token(monkeypatch):
    class FakeClient:
        def __init__(self, url):
            pass

        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key="wrong-secret")

    monkeypatch.setattr(auth, "PyJWKClient", FakeClient)
    with pytest.raises(HTTPException) as error:
        auth.verify_oidc_token_from_jwks(
            _token(),
            jwks_url="https://issuer.example/jwks",
            issuer="https://issuer.example",
            audience="nikway-api",
            algorithms=["HS256"],
        )
    assert error.value.status_code == 401


def test_jwks_provider_failure_fails_closed(monkeypatch):
    class FakeClient:
        def __init__(self, url):
            pass

        def get_signing_key_from_jwt(self, token):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(auth, "PyJWKClient", FakeClient)
    with pytest.raises(HTTPException) as error:
        auth.verify_oidc_token_from_jwks(
            "not-a-token",
            jwks_url="https://issuer.example/jwks",
            issuer="https://issuer.example",
            audience="nikway-api",
        )
    assert error.value.status_code == 401
    assert error.value.detail == "Invalid OIDC token"


def test_jwks_verifier_requires_endpoint():
    with pytest.raises(HTTPException) as error:
        auth.verify_oidc_token_from_jwks(
            "not-a-token",
            jwks_url="",
            issuer="https://issuer.example",
            audience="nikway-api",
        )
    assert error.value.status_code == 401
