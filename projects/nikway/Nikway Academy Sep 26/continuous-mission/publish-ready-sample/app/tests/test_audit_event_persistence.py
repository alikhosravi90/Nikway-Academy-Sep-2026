from app.repositories import record_audit_event, record_event


def test_event_and_audit_fallback_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert record_event("org-1", {}, "test", {}, {}) is None
    assert record_audit_event("org-1", None, "test", "Test", "id-1", None, {}) is None
