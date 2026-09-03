import pytest
from fastapi import HTTPException

from app.authorization import (
    INVITATION_CREATE,
    MASTER_CREATE,
    MASTER_READ,
    MASTER_ROLLBACK,
    authorize,
)


def test_deny_by_default_and_401_403_semantics():
    with pytest.raises(HTTPException) as unauthenticated:
        authorize(None, MASTER_READ)
    assert unauthenticated.value.status_code == 401

    with pytest.raises(HTTPException) as no_permission:
        authorize({"organization_id": "org-a", "role": "learner"}, MASTER_CREATE)
    assert no_permission.value.status_code == 403

    with pytest.raises(HTTPException) as unknown_role:
        authorize({"organization_id": "org-a", "role": "unknown"}, MASTER_READ)
    assert unknown_role.value.status_code == 403


def test_authorized_roles_and_privilege_separation():
    assert authorize({"organization_id": "org-a", "role": "org_admin"}, MASTER_CREATE)
    assert authorize({"organization_id": "org-a", "role": "assessor"}, MASTER_READ)
    with pytest.raises(HTTPException):
        authorize({"organization_id": "org-a", "role": "org_admin"}, MASTER_ROLLBACK)
    assert authorize({"organization_id": "org-a", "role": "nikway_admin"}, MASTER_ROLLBACK)


def test_cross_organization_request_and_resource_are_denied():
    membership = {"organization_id": "org-a", "role": "org_admin"}
    with pytest.raises(HTTPException) as context_error:
        authorize(membership, MASTER_CREATE, requested_organization_id="org-b")
    assert context_error.value.status_code == 403
    with pytest.raises(HTTPException) as resource_error:
        authorize(membership, MASTER_READ, resource_organization_id="org-b")
    assert resource_error.value.status_code == 403


def test_authorization_decision_is_auditable_without_secrets():
    decisions = []
    membership = {"organization_id": "org-a", "role": "org_admin"}
    authorize(membership, INVITATION_CREATE, audit=decisions.append)
    assert decisions[0].allowed is True
    assert decisions[0].permission == INVITATION_CREATE
    assert decisions[0].organization_id == "org-a"
    assert "secret" not in repr(decisions[0]).lower()
