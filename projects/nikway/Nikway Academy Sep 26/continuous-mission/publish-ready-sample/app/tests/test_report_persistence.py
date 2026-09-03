from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_progress_report_uses_repository(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.read_progress_report",
        lambda organization_id: {
            "organization_id": organization_id,
            "assignments": 2,
            "assessments": 1,
            "progressions": 1,
        },
    )

    response = client.get(
        "/api/v1/reports/progress",
        headers={"X-Organization-Id": "org-1"},
    )

    assert response.status_code == 200
    assert response.json()["organization_id"] == "org-1"
    assert response.json()["progressions"] == 1


def test_production_progress_report_returns_service_unavailable_on_failure(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr("app.main.read_progress_report", lambda *args: None)

    response = client.get(
        "/api/v1/reports/progress",
        headers={"X-Organization-Id": "org-2"},
    )

    assert response.status_code == 503
