from typing import Any

from fastapi import Header, HTTPException

try:
    import jwt
    from jwt import PyJWKClient
except ImportError:  # pragma: no cover - installed in the container image
    jwt = None
    PyJWKClient = None


def verify_oidc_token(
    token: str,
    *,
    signing_key: str,
    issuer: str,
    audience: str,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    """Verify a provider-issued JWT before resolving organization membership."""
    if not token or not signing_key or not issuer or not audience:
        raise HTTPException(401, "OIDC configuration or token is missing")
    if jwt is None:
        raise HTTPException(503, "OIDC dependency is unavailable")
    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=algorithms or ["HS256"],
            issuer=issuer,
            audience=audience,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid OIDC token") from exc
    return claims


def verify_oidc_token_from_jwks(
    token: str,
    *,
    jwks_url: str,
    issuer: str,
    audience: str,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve a rotating provider key from JWKS and verify the JWT claims."""
    if not token or not jwks_url:
        raise HTTPException(401, "OIDC token or JWKS URL is missing")
    if PyJWKClient is None:
        raise HTTPException(503, "OIDC dependency is unavailable")
    try:
        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        return verify_oidc_token(
            token,
            signing_key=signing_key.key,
            issuer=issuer,
            audience=audience,
            algorithms=algorithms or ["RS256"],
        )
    except HTTPException:
        raise
    except (jwt.PyJWTError, OSError, TimeoutError) as exc:
        raise HTTPException(401, "Invalid OIDC token") from exc
    except Exception as exc:
        # JWKS clients may expose provider/network failures through
        # implementation-specific exceptions. Never let them escape as 500.
        raise HTTPException(401, "Invalid OIDC token") from exc


def resolve_membership(
    claims: dict[str, Any], memberships: dict[str, dict[str, str]]
) -> dict[str, str]:
    """Map verified OIDC subject to an organization membership."""
    subject = str(claims.get("sub", ""))
    membership = memberships.get(subject)
    if not membership:
        raise HTTPException(403, "Organization membership is required")
    return membership


def bearer_token(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Bearer token is required")
    return authorization.split(" ", 1)[1].strip()


def resolve_request_membership(
    authorization: str | None,
    *,
    jwks_url: str,
    issuer: str,
    audience: str,
) -> dict[str, str]:
    claims = verify_oidc_token_from_jwks(
        bearer_token(authorization),
        jwks_url=jwks_url,
        issuer=issuer,
        audience=audience,
    )
    organization_id = claims.get("organization_id") or claims.get("org_id")
    role = claims.get("role")
    if not organization_id or not role:
        raise HTTPException(403, "Organization and role claims are required")
    return {
        "subject": str(claims["sub"]),
        "organization_id": str(organization_id),
        "role": str(role),
    }
