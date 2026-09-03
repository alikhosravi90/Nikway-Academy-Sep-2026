from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_development_readiness_is_not_ready_without_external_dependencies(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "development")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("OIDC_ISSUER_URL", raising=False)
    monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("S3_ENDPOINT_URL", raising=False)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "not_ready"


def test_production_readiness_requires_all_dependencies(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("OIDC_AUDIENCE", "nikway-api")
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://storage.example")

    response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["dependencies"]["database"]["status"] == "not_configured"


def test_cors_does_not_allow_wildcard(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://pilot.example")
    response = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") != "*"
