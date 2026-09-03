from types import SimpleNamespace

import app.storage as storage_module
from app.storage import (
    OrphanCleanupWorker,
    S3Storage,
    UploadPlan,
    cleanup_after_persistence_failure,
    persist_uploaded_evidence,
)
from fastapi.testclient import TestClient
from app.main import app


class FakeS3Client:
    def __init__(self):
        self.put_calls = []
        self.delete_calls = []

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)

    def delete_object(self, **kwargs):
        self.delete_calls.append(kwargs)


def test_s3_client_writes_checksum_and_scoped_key(monkeypatch):
    fake = FakeS3Client()
    monkeypatch.setattr(
        storage_module,
        "boto3",
        SimpleNamespace(client=lambda *args, **kwargs: fake),
    )
    storage = S3Storage("http://storage.local", "nikway-evidence")
    plan = UploadPlan("organizations/org-1/evidence/e-1/a.txt", "text/plain", 4, "abcd")

    reference = storage.put(plan, b"data")

    assert reference.startswith("s3://nikway-evidence/")
    assert fake.put_calls[0]["ChecksumSHA256"] == "abcd"


def test_orphan_cleanup_worker_deletes_all_keys():
    class FakeStorage:
        def __init__(self):
            self.deleted = []

        def delete(self, key):
            self.deleted.append(key)

    storage = FakeStorage()
    worker = OrphanCleanupWorker(storage)
    assert worker.cleanup(["a", "b"]) == 2
    assert storage.deleted == ["a", "b"]


def test_upload_rollback_deletes_object_reference():
    class FakeStorage:
        def __init__(self):
            self.deleted = []

        def delete(self, key):
            self.deleted.append(key)

    storage = FakeStorage()
    result = cleanup_after_persistence_failure(storage, "organizations/org-1/evidence/e-1/a.txt")
    assert result["status"] == "deleted_after_rollback"
    assert storage.deleted == ["organizations/org-1/evidence/e-1/a.txt"]


def test_upload_endpoint_uses_real_storage_boundary(monkeypatch):
    fake = FakeS3Client()
    monkeypatch.setattr(
        storage_module,
        "boto3",
        SimpleNamespace(client=lambda *args, **kwargs: fake),
    )
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://storage.local")
    monkeypatch.setenv("S3_BUCKET", "nikway-evidence")

    response = TestClient(app).post(
        "/api/v1/assignments/assignment-1/evidence/upload",
        headers={"X-Organization-Id": "org-1"},
        params={"step_id": "step-1"},
        files={"file": ("map.txt", b"boundary map", "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"
    assert response.json()["object_storage_ref"].startswith("s3://nikway-evidence/")
    assert fake.put_calls[0]["Bucket"] == "nikway-evidence"
