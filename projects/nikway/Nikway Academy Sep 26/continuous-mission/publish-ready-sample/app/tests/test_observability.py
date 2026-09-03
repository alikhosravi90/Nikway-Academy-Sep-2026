from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_correlation_id_is_preserved():
    response = client.get("/health", headers={"X-Correlation-Id": "corr-20260902-001"})
    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"] == "corr-20260902-001"


def test_correlation_id_is_generated_when_missing():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"]
