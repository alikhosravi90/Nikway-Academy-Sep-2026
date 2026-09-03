# V1 Evidence Upload Security Policy

Evidence files are accepted only after authentication, authorization, size validation, MIME validation, and checksum calculation.

Required flow:

```text
Authenticate → Authorize Organization → Validate Size/Type
→ Calculate SHA-256 → Upload to S3-compatible Storage
→ Persist Object Reference → Emit Audit Event
```

The application never stores uploaded files on its local filesystem. File content is not logged. Object storage access uses short-lived signed URLs and organization-scoped object keys.

Rejected conditions:

- Missing organization membership
- File larger than 25 MB
- Unsupported MIME type
- Missing checksum
- Object key outside the organization prefix
- Upload failure after database record creation

If upload succeeds but database persistence fails, the object is marked orphaned and queued for cleanup; it is never silently reused.
