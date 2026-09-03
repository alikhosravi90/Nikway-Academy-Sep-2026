# V1 application sample

This sample currently runs the vertical slice in memory so it can be tested
without external services. `app.persistence` provides the production boundary
for PostgreSQL health checks and transaction-local tenant context. `settings.py`
centralizes environment configuration and `repositories.py` provides the
transaction seam for SQL-backed handlers.

When database-backed handlers are introduced, every request transaction must:

1. resolve and authorize the caller's organization;
2. call `set_organization_context(connection, organization_id)`;
3. use a non-owner runtime role;
4. commit only after the domain operation and its audit/event write succeed.

The in-memory implementation is not production persistence. Production and
staging must provide `DATABASE_URL`; the release gate
must remain `ready_for_review` until database-backed handlers and end-to-end
OIDC/object-storage tests are complete.

The organization creation path now has an explicit production repository seam
and API tests for both successful persistence and controlled database failure.

`repositories.py` also exposes durable event and audit-event writers. These
writers use the same transaction-local organization context as domain writes;
the current endpoint sample still needs orchestration-level wiring so each
domain mutation commits its event and audit record atomically.

`auth.py` provides the OIDC JWT verification seam. Production must replace the
test signing key with provider JWKS/key rotation and map the verified `sub` to
an organization membership before allowing tenant-scoped operations.
The JWKS verifier and membership resolver are now implemented as explicit
boundaries; endpoint dependency injection remains the next integration step.

`storage.py` defines the S3-compatible upload boundary: organization-scoped
object keys, a 25 MB limit, allowlisted content types, SHA-256 checksums, and
an explicit orphan-cleanup queue marker.

`scripts/generate_openapi.py` exports the FastAPI implementation schema, while
`scripts/contract_diff.py` reads the YAML contract and checks that every
contract path exists in code.

The CI workflow installs `requirements.txt` before running tests, so optional
local skips caused by missing `PyJWT` or `psycopg` do not hide dependency
failures in the release pipeline.

CI also provisions PostgreSQL 16, applies `db/v1_schema.sql`, and runs the
tenant-context test against the service before the local fallback test pass.
The repository integration test additionally verifies organization creation
and multi-step journey persistence when `DATABASE_URL` is available.

`/health/ready` reports whether production-required database, OIDC, and object
storage configuration is available. It intentionally stays `not_ready` until
all required dependencies are configured and the database is reachable.

Every response receives an `X-Correlation-Id`; callers may provide one to
connect API activity with event and audit records.

`record_trace` provides the atomic PostgreSQL seam for writing an event and its
audit record with the same organization and correlation context.
