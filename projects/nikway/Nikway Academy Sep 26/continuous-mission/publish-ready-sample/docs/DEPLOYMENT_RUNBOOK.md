# V1 Deployment Runbook

## Preconditions

- PostgreSQL is provisioned.
- `nikway_runtime` is a non-superuser application role.
- OIDC issuer, audience, and JWKS settings are configured.
- S3-compatible storage and scoped credentials are configured.
- TLS terminates at the deployment boundary.
- Security scan has no unresolved critical or high finding.

## Deployment

1. Build one application container.
2. Apply versioned PostgreSQL migrations.
3. Start the container with environment-provided configuration.
4. Verify `/health` and authenticated API access.
5. Run the V1 smoke test.
6. Record image digest, migration version, operator, and evidence references.

## Rollback

Stop traffic, restore the previous image, and roll back only through a tested backward-compatible migration path. Never delete production data to resolve a deployment failure.

## Stop Conditions

Stop deployment if OIDC validation fails, the application connects as superuser, migrations fail, TLS is absent, or the smoke test fails twice.
