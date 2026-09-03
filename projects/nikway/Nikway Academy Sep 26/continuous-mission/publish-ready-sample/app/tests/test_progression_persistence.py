from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_progression_uses_repository(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_progression_with_trace",
        lambda organization_id, assessment_id, correlation_id: {
            "id": "00000000-0000-0000-0000-000000000044",
            "organization_id": organization_id,
            "assessment_id": assessment_id,
            "status": "advanced",
        },
    )

    response = client.post(
        "/api/v1/assessment-results/assessment-1/progression",
        headers={
            "X-Organization-Id": "org-1",
            "Idempotency-Key": "progression-production-1",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "advanced"


def test_production_progression_rejects_unavailable_or_unaccepted_assessment(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr("app.main.persist_progression_with_trace", lambda *args: None)

    response = client.post(
        "/api/v1/assessment-results/assessment-2/progression",
        headers={
            "X-Organization-Id": "org-2",
            "Idempotency-Key": "progression-production-2",
        },
    )

    assert response.status_code == 409
