"""Small, deny-by-default authorization boundary for the modular monolith."""

from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException


MASTER_READ = "master.read"
MASTER_CREATE = "master.create"
MASTER_VERSION_CREATE = "master.version.create"
MASTER_ROLLBACK = "master.rollback"
INVITATION_CREATE = "invitation.create"

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "nikway_admin": frozenset(
        {
            MASTER_READ,
            MASTER_CREATE,
            MASTER_VERSION_CREATE,
            MASTER_ROLLBACK,
            INVITATION_CREATE,
        }
    ),
    "org_admin": frozenset({MASTER_READ, MASTER_CREATE, MASTER_VERSION_CREATE, INVITATION_CREATE}),
    "assessor": frozenset({MASTER_READ}),
    "learner": frozenset(),
}


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    permission: str
    organization_id: str | None
    role: str | None
    reason: str


AuditAuthorization = Callable[[AuthorizationDecision], None]


def authorize(
    membership: dict[str, str] | None,
    permission: str,
    *,
    requested_organization_id: str | None = None,
    resource_organization_id: str | None = None,
    audit: AuditAuthorization | None = None,
) -> dict[str, str]:
    """Authorize before service/repository execution; default is deny."""
    role = membership.get("role") if membership else None
    organization_id = membership.get("organization_id") if membership else None
    reason = "allowed"
    allowed = bool(role and organization_id and permission in ROLE_PERMISSIONS.get(role, frozenset()))
    if allowed and requested_organization_id and requested_organization_id != organization_id:
        allowed = False
        reason = "organization_context_mismatch"
    if allowed and resource_organization_id and resource_organization_id != organization_id:
        allowed = False
        reason = "resource_organization_mismatch"
    if not membership:
        reason = "authentication_required"
    elif role not in ROLE_PERMISSIONS:
        reason = "unknown_role"
    elif permission not in ROLE_PERMISSIONS[role]:
        reason = "permission_denied"
    decision = AuthorizationDecision(allowed, permission, organization_id, role, reason)
    if audit:
        audit(decision)
    if not allowed:
        status = 401 if reason == "authentication_required" else 403
        raise HTTPException(status, "Authorization denied")
    return membership


def require_permission(permission: str, membership_dependency):
    """Create a FastAPI dependency after the existing membership dependency."""

    def dependency(membership: dict[str, str] = Depends(membership_dependency)) -> dict[str, str]:
        return authorize(membership, permission)

    return dependency
