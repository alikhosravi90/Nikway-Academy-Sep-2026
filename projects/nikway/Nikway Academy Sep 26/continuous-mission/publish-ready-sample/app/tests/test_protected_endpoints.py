from fastapi.testclient import TestClient

from app.main import app


def test_assignment_requires_oidc_when_auth_is_enabled(monkeypatch):
    monkeypatch.setenv("NIKWAY_REQUIRE_AUTH", "true")
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("OIDC_AUDIENCE", "nikway-api")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example/jwks")

    response = TestClient(app).post(
        "/api/v1/journeys/journey-1/assignments",
        headers={
            "X-Organization-Id": "org-1",
            "Idempotency-Key": "protected-assignment-1",
        },
        json={"learner_id": "learner-1"},
    )
    assert response.status_code == 401
