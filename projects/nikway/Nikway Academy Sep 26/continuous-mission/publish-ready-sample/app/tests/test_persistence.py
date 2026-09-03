import os

import pytest

from app.persistence import database_engine, database_status, set_organization_context


def test_database_fallback_without_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_engine() is None
    assert database_status() == {"mode": "in_memory", "status": "not_configured"}


def test_tenant_context_is_transaction_local_when_database_is_configured():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured")

    engine = database_engine()
    assert engine is not None
    if database_status()["status"] != "ready":
        pytest.skip("Configured DATABASE_URL is not reachable")
    with engine.begin() as connection:
        set_organization_context(
            connection, "00000000-0000-0000-0000-000000000001"
        )
        value = connection.exec_driver_sql(
            "SELECT current_setting('app.current_org_id', true)"
        ).scalar_one()
        assert value == "00000000-0000-0000-0000-000000000001"
