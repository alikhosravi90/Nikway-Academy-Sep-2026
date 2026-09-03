from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invitation_is_queued_for_matching_organization():
    response = client.post(
        "/api/v1/organizations/org-1/invitations",
        headers={"X-Organization-Id": "org-1"},
        json={"email": "USER@EXAMPLE.COM", "role": "learner"},
    )

    assert response.status_code == 202
    assert response.json()["email"] == "user@example.com"


def test_invitation_rejects_cross_organization_context():
    response = client.post(
        "/api/v1/organizations/org-1/invitations",
        headers={"X-Organization-Id": "org-2"},
        json={"email": "user@example.com"},
    )

    assert response.status_code == 403
