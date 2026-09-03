from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_assignment_returns_trace_context(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_assignment_with_trace",
        lambda organization_id, journey_id, learner_id, correlation_id: {
            "id": "assignment-traced",
            "organization_id": organization_id,
            "journey_id": journey_id,
            "learner_id": learner_id,
            "status": "active",
            "event": {"context": {"correlation_id": correlation_id}},
        },
    )

    response = client.post(
        "/api/v1/journeys/journey-1/assignments",
        headers={
            "X-Organization-Id": "org-1",
            "Idempotency-Key": "assignment-trace-1",
            "X-Correlation-Id": "corr-assignment-1",
        },
        json={"learner_id": "learner-1"},
    )

    assert response.status_code == 201
    assert response.json()["event"]["context"]["correlation_id"] == "corr-assignment-1"
