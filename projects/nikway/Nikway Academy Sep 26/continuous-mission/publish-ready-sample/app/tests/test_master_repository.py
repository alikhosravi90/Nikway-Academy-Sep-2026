import os
from uuid import uuid4

import pytest

from app.master_repository import persist_master, persist_master_version, retrieve_master
from app.master_system import MasterDefinition, MasterSystemError, MasterVersion
from app.persistence import database_status


def _master() -> MasterDefinition:
    version = MasterVersion(
        version="1.0.0",
        schema={"title": "string"},
        required_fields=("title",),
        defaults={"status": "draft"},
    )
    return MasterDefinition(
        id="MASTER-PERSISTED-001",
        name="Persisted Course",
        object_type="course",
        current_version="1.0.0",
        versions={"1.0.0": version},
    )


pytestmark = pytest.mark.integration


def _ready() -> bool:
    return bool(os.getenv("DATABASE_URL")) and database_status()["status"] == "ready"


def test_master_persists_and_retrieves_from_postgresql():
    if not _ready():
        pytest.skip("PostgreSQL runtime is not configured/reachable")
    master = _master()
    master.id = f"MASTER-PERSISTED-{uuid4()}"
    persist_master(master)
    restored = retrieve_master(master.id)
    assert restored == master


def test_master_version_is_append_only_and_pointer_advances():
    if not _ready():
        pytest.skip("PostgreSQL runtime is not configured/reachable")
    master = _master()
    master.id = f"MASTER-PERSISTED-{uuid4()}"
    persist_master(master)
    version = MasterVersion(
        version="2.0.0",
        schema={"title": "string", "owner": "string"},
        required_fields=("title", "owner"),
    )
    updated = persist_master_version(master.id, version)
    assert updated is not None
    assert updated.current_version == "2.0.0"
    assert set(updated.versions) == {"1.0.0", "2.0.0"}
    with pytest.raises(MasterSystemError):
        persist_master_version(master.id, version)
    restored = retrieve_master(master.id)
    assert restored is not None
    assert restored.current_version == "2.0.0"
    assert set(restored.versions) == {"1.0.0", "2.0.0"}
