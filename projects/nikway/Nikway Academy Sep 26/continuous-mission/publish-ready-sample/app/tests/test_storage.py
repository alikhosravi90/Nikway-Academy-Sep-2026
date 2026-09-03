import hashlib

import pytest
from fastapi import HTTPException

from app.storage import orphan_cleanup_key, plan_upload


def test_upload_plan_uses_organization_scoped_key_and_checksum():
    content = b"evidence"
    plan = plan_upload("org-1", "evidence-1", "map.txt", content, "text/plain")

    assert plan.object_key == "organizations/org-1/evidence/evidence-1/map.txt"
    assert plan.checksum_sha256 == hashlib.sha256(content).hexdigest()
    assert plan.size_bytes == len(content)


@pytest.mark.parametrize(
    "filename,content_type",
    [("script.exe", "application/octet-stream"), ("image.png", "text/plain")],
)
def test_upload_plan_rejects_unsupported_type(filename, content_type):
    with pytest.raises(HTTPException) as error:
        plan_upload("org-1", "evidence-1", filename, b"data", content_type)
    assert error.value.status_code == 415


def test_upload_plan_rejects_oversized_content():
    with pytest.raises(HTTPException) as error:
        plan_upload("org-1", "evidence-1", "large.txt", b"x" * (25 * 1024 * 1024 + 1), "text/plain")
    assert error.value.status_code == 413


def test_orphan_cleanup_is_explicit():
    assert orphan_cleanup_key("organizations/org-1/evidence/e-1/file.txt") == {
        "object_key": "organizations/org-1/evidence/e-1/file.txt",
        "status": "queued_for_cleanup",
    }
