from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_assignment_uses_repository(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_assignment_with_trace",
        lambda organization_id, journey_id, learner_id, correlation_id: {
            "id": "00000000-0000-0000-0000-000000000077",
            "organization_id": organization_id,
            "journey_id": journey_id,
            "learner_id": learner_id,
            "status": "active",
        },
    )

    response = client.post(
        "/api/v1/journeys/journey-1/assignments",
        headers={
            "X-Organization-Id": "org-1",
            "Idempotency-Key": "assignment-production-1",
        },
        json={"learner_id": "learner-1"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "active"


def test_production_assignment_failure_is_controlled(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr("app.main.persist_assignment_with_trace", lambda *args: None)

    response = client.post(
        "/api/v1/journeys/journey-2/assignments",
        headers={
            "X-Organization-Id": "org-2",
            "Idempotency-Key": "assignment-production-2",
        },
        json={"learner_id": "learner-2"},
    )

    assert response.status_code == 503
