from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_organization_uses_repository(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_organization",
        lambda name: {"id": "00000000-0000-0000-0000-000000000099", "name": name},
    )

    response = client.post(
        "/api/v1/organizations",
        json={"name": "Production Pilot"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": "00000000-0000-0000-0000-000000000099",
        "name": "Production Pilot",
    }


def test_production_organization_returns_service_unavailable_on_persistence_failure(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr("app.main.persist_organization", lambda name: None)

    response = client.post(
        "/api/v1/organizations",
        json={"name": "Unavailable Pilot"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Database persistence is unavailable"
