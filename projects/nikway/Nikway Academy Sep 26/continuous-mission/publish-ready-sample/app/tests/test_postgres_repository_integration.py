import os

import pytest

from app.persistence import database_status
from app.repositories import create_journey, create_organization


pytestmark = pytest.mark.integration


def _database_ready() -> bool:
    return bool(os.getenv("DATABASE_URL"))


def test_postgres_organization_and_journey_transaction():
    if not _database_ready():
        pytest.skip("DATABASE_URL is not configured")
    if database_status()["status"] != "ready":
        pytest.skip("Configured DATABASE_URL is not reachable")

    organization = create_organization("Repository Integration Org")
    assert organization is not None

    journey = create_journey(
        organization["id"],
        "Repository Integration Journey",
        "Persisted in PostgreSQL",
        [{"title": "Step one"}, {"title": "Step two"}],
    )

    assert journey is not None
    assert journey["organization_id"] == organization["id"]
    assert [step["title"] for step in journey["steps"]] == ["Step one", "Step two"]
