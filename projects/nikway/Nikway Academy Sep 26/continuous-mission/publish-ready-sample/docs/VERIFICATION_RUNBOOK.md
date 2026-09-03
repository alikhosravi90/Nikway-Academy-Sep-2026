# V1 Verification Runbook

## Scope

Run verification in the isolated V1 PostgreSQL compose project. Do not attach tests to an existing platform database.

## Commands

```powershell
$env:NIKWAY_POSTGRES_PASSWORD = 'local-only-value'
docker compose -f docker-compose.full-v1.yml up -d
docker compose -f docker-compose.full-v1.yml ps
```

## Verification

1. Confirm the PostgreSQL health check is passing.
2. Apply the RLS test plan with two organizations.
3. Run the API integration tests against the isolated database.
4. Create a backup and execute `RESTORE_RUNBOOK.md`.
5. Attach test output and backup checksum to the release evidence.

## Stop Conditions

- Stop if the container is unhealthy.
- Stop after two retries of the same failing test.
- Stop if a test targets a non-isolated database.
- Mark `blocked_for_human` if OIDC credentials or object-storage credentials are unavailable.
