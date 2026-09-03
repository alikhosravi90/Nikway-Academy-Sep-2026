from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_in_memory_fallback_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.get("/health/dependencies")
    assert response.status_code == 200
    assert response.json()["database"]["mode"] == "in_memory"
