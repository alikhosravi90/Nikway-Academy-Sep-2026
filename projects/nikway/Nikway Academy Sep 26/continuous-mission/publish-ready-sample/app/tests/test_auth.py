from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

pytest.importorskip("jwt")
import jwt

from app.auth import resolve_membership, verify_oidc_token


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


def test_oidc_token_verification_accepts_valid_claims():
    claims = verify_oidc_token(
        _token(),
        signing_key="test-secret",
        issuer="https://issuer.example",
        audience="nikway-api",
    )

    assert claims["sub"] == "user-1"


@pytest.mark.parametrize(
    "overrides",
    [{"aud": "other-api"}, {"iss": "https://other.example"}, {"exp": datetime.now(timezone.utc) - timedelta(minutes=1)}],
)
def test_oidc_token_verification_rejects_invalid_claims(overrides):
    with pytest.raises(HTTPException) as error:
        verify_oidc_token(
            _token(**overrides),
            signing_key="test-secret",
            issuer="https://issuer.example",
            audience="nikway-api",
        )
    assert error.value.status_code == 401


def test_oidc_token_verification_requires_configuration():
    with pytest.raises(HTTPException) as error:
        verify_oidc_token(
            "not-a-token",
            signing_key="",
            issuer="",
            audience="",
        )
    assert error.value.status_code == 401


def test_membership_mapping_uses_verified_subject():
    membership = resolve_membership(
        {"sub": "user-1"},
        {"user-1": {"organization_id": "org-1", "role": "org_admin"}},
    )
    assert membership == {"organization_id": "org-1", "role": "org_admin"}


def test_membership_mapping_denies_unknown_subject():
    with pytest.raises(HTTPException) as error:
        resolve_membership({"sub": "unknown"}, {})
    assert error.value.status_code == 403
