from app.settings import load_settings


def test_development_settings_allow_local_fallback(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "development")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000, https://pilot.example")

    settings = load_settings()

    assert settings.database_required is False
    assert settings.database_url == ""
    assert settings.cors_allowed_origins == (
        "http://localhost:3000",
        "https://pilot.example",
    )


def test_production_settings_require_database(monkeypatch):
    monkeypatch.setenv("NIKWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://runtime@example/nikway")

    settings = load_settings()

    assert settings.database_required is True
    assert settings.database_url.startswith("postgresql+psycopg://")
