from app.main import make_event
from app.repositories import record_trace


def test_event_contains_correlation_id():
    event = make_event("journey_assigned", "assignment-1", "JourneyAssignment", "org-1", "corr-1")
    assert event["context"]["correlation_id"] == "corr-1"


def test_trace_fallback_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert record_trace(
        "org-1",
        "corr-1",
        {"id": "system"},
        "created",
        "Journey",
        "journey-1",
        None,
        {"title": "Test"},
        "journey_created",
        {"id": "journey-1"},
        {"organization_id": "org-1"},
    ) is None
