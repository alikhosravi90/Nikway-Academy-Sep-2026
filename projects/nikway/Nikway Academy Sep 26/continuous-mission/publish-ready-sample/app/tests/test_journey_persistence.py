from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_production_journey_uses_repository(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr(
        "app.main.persist_journey_with_trace",
        lambda organization_id, title, description, steps, correlation_id: {
            "id": "00000000-0000-0000-0000-000000000088",
            "organization_id": organization_id,
            "title": title,
            "description": description,
            "steps": steps,
        },
    )

    response = client.post(
        "/api/v1/journeys",
        headers={"X-Organization-Id": "00000000-0000-0000-0000-000000000001"},
        json={"title": "Journey", "description": "Pilot", "steps": [{"title": "Start"}]},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Journey"
    assert response.json()["steps"] == [{"title": "Start"}]


def test_production_journey_returns_service_unavailable_on_persistence_failure(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")
    monkeypatch.setattr("app.main.persist_journey_with_trace", lambda *args: None)

    response = client.post(
        "/api/v1/journeys",
        headers={"X-Organization-Id": "00000000-0000-0000-0000-000000000001"},
        json={"title": "Journey", "steps": [{"title": "Start"}]},
    )

    assert response.status_code == 503
