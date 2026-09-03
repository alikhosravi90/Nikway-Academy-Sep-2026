import hashlib
import mimetypes
import os
from dataclasses import dataclass

from fastapi import HTTPException

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None


ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "application/pdf",
    "image/png",
    "image/jpeg",
}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class UploadPlan:
    object_key: str
    content_type: str
    size_bytes: int
    checksum_sha256: str


def plan_upload(
    organization_id: str,
    evidence_id: str,
    filename: str,
    content: bytes,
    content_type: str | None = None,
) -> UploadPlan:
    if not organization_id or not evidence_id or not filename:
        raise HTTPException(422, "Upload identity is required")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Upload exceeds the 25 MB limit")
    resolved_type = content_type or mimetypes.guess_type(filename)[0]
    if resolved_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, "Unsupported upload type")
    guessed_type = mimetypes.guess_type(filename)[0]
    if content_type and guessed_type and content_type != guessed_type:
        raise HTTPException(415, "Upload type does not match filename")
    safe_name = filename.replace("\\", "/").split("/")[-1]
    object_key = f"organizations/{organization_id}/evidence/{evidence_id}/{safe_name}"
    checksum = hashlib.sha256(content).hexdigest()
    return UploadPlan(
        object_key=object_key,
        content_type=resolved_type,
        size_bytes=len(content),
        checksum_sha256=checksum,
    )


def orphan_cleanup_key(object_key: str) -> dict[str, str]:
    return {"object_key": object_key, "status": "queued_for_cleanup"}


class S3Storage:
    def __init__(self, endpoint_url: str, bucket: str):
        if boto3 is None:
            raise RuntimeError("boto3 is required for S3 storage")
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

    def put(self, plan: UploadPlan, content: bytes) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=plan.object_key,
            Body=content,
            ContentType=plan.content_type,
            ChecksumSHA256=plan.checksum_sha256,
        )
        return f"s3://{self.bucket}/{plan.object_key}"

    def delete(self, object_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=object_key)


class OrphanCleanupWorker:
    def __init__(self, storage: S3Storage):
        self.storage = storage

    def cleanup(self, object_keys: list[str]) -> int:
        for object_key in object_keys:
            self.storage.delete(object_key)
        return len(object_keys)


def persist_uploaded_evidence(storage: S3Storage, plan: UploadPlan, content: bytes) -> str:
    """Upload first; callers persist the returned reference in the same workflow."""
    try:
        return storage.put(plan, content)
    except Exception:
        # The object was not confirmed, so no database reference may be created.
        raise


def cleanup_after_persistence_failure(storage: S3Storage, object_key: str) -> dict[str, str]:
    storage.delete(object_key)
    return orphan_cleanup_key(object_key) | {"status": "deleted_after_rollback"}
