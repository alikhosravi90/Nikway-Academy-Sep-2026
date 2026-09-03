from fastapi.testclient import TestClient

from app.main import app


def test_production_progression_preserves_correlation_id(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_progression_with_trace",
        lambda organization_id, assessment_id, correlation_id: {
            "id": "progression-traced",
            "organization_id": organization_id,
            "assessment_id": assessment_id,
            "status": "advanced",
            "event": {"context": {"correlation_id": correlation_id}},
        },
    )

    response = TestClient(app).post(
        "/api/v1/assessment-results/assessment-1/progression",
        headers={
            "X-Organization-Id": "org-1",
            "Idempotency-Key": "progression-trace-1",
            "X-Correlation-Id": "corr-progression-1",
        },
    )

    assert response.status_code == 201
    assert response.json()["event"]["context"]["correlation_id"] == "corr-progression-1"
