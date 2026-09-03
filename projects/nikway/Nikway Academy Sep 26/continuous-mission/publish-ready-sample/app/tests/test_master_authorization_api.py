from fastapi.testclient import TestClient

from app.main import app, master_service
from app.master_system import MasterRegistry


def _payload(master_id="MASTER-API-001"):
    return {
        "id": master_id,
        "name": "Course",
        "object_type": "course",
        "current_version": "1.0.0",
        "version": {"version": "1.0.0", "schema": {"title": "string"}},
    }


def _client(membership):
    app.dependency_overrides[__import__("app.main", fromlist=["require_master_membership"]).require_master_membership] = (
        lambda: membership
    )
    return TestClient(app)


def test_master_api_denies_anonymous_and_allows_org_admin():
    app.dependency_overrides.clear()
    # The real dependency remains protected and returns 401 without a bearer token.
    response = TestClient(app).get(
        "/api/v1/masters", headers={"X-Organization-Id": "org-a"}
    )
    assert response.status_code == 401

    master_service.registry = MasterRegistry()
    client = _client({"organization_id": "org-a", "role": "org_admin"})
    try:
        response = client.post(
            "/api/v1/masters",
            headers={"X-Organization-Id": "org-a"},
            json=_payload(),
        )
        assert response.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_master_api_denies_missing_permission_and_cross_org_context():
    master_service.registry = MasterRegistry()
    client = _client({"organization_id": "org-a", "role": "learner"})
    try:
        denied = client.post(
            "/api/v1/masters",
            headers={"X-Organization-Id": "org-a"},
            json=_payload("MASTER-DENIED-001"),
        )
        assert denied.status_code == 403
        cross_org = client.get(
            "/api/v1/masters",
            headers={"X-Organization-Id": "org-b"},
        )
        assert cross_org.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_master_api_enforces_permission_before_duplicate_mutation():
    master_service.registry = MasterRegistry()
    client = _client({"organization_id": "org-a", "role": "org_admin"})
    try:
        first = client.post(
            "/api/v1/masters",
            headers={"X-Organization-Id": "org-a"},
            json=_payload("MASTER-DUP-001"),
        )
        duplicate = client.post(
            "/api/v1/masters",
            headers={"X-Organization-Id": "org-a"},
            json=_payload("MASTER-DUP-001"),
        )
        assert first.status_code == 201
        assert duplicate.status_code == 409
        assert len(master_service.registry.list_masters()) == 1
    finally:
        app.dependency_overrides.clear()
