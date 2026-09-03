from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_evidence_uses_repository(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_evidence_with_trace",
        lambda *args: {
            "id": "00000000-0000-0000-0000-000000000066",
            "organization_id": args[0],
            "assignment_id": args[1],
            "evidence_type": args[3],
            "content": args[4],
            "status": "submitted",
        },
    )

    response = client.post(
        "/api/v1/assignments/assignment-1/evidence",
        headers={
            "X-Organization-Id": "org-1",
            "Idempotency-Key": "evidence-production-1",
        },
        json={
            "step_id": "step-1",
            "evidence_type": "text",
            "content": "Boundary map",
            "checksum": "sha256:example",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "submitted"


def test_production_evidence_rejects_empty_payload(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")

    response = client.post(
        "/api/v1/assignments/assignment-2/evidence",
        headers={
            "X-Organization-Id": "org-2",
            "Idempotency-Key": "evidence-production-2",
        },
        json={"step_id": "step-1", "evidence_type": "file"},
    )

    assert response.status_code == 422
