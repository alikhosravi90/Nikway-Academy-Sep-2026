from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_assessment_uses_repository(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_assessment_with_trace",
        lambda organization_id, evidence_id, criterion_results, verdict, comments, correlation_id: {
            "id": "00000000-0000-0000-0000-000000000055",
            "organization_id": organization_id,
            "evidence_id": evidence_id,
            "criterion_results": criterion_results,
            "verdict": verdict,
            "comments": comments,
        },
    )

    response = client.post(
        "/api/v1/evidence/evidence-1/assessment",
        headers={
            "X-Organization-Id": "org-1",
            "Idempotency-Key": "assessment-production-1",
        },
        json={
            "criterion_results": [{"criterion": "clarity", "accepted": True}],
            "verdict": "accepted",
            "comments": "Ready",
        },
    )

    assert response.status_code == 201
    assert response.json()["verdict"] == "accepted"


def test_production_assessment_rejects_invalid_verdict(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")

    response = client.post(
        "/api/v1/evidence/evidence-2/assessment",
        headers={
            "X-Organization-Id": "org-2",
            "Idempotency-Key": "assessment-production-2",
        },
        json={"criterion_results": [], "verdict": "maybe"},
    )

    assert response.status_code == 422
