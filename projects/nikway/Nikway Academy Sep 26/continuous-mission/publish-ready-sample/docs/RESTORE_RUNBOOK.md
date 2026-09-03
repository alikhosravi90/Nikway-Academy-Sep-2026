# PostgreSQL Restore Runbook

## Purpose

Restore a daily backup into an isolated PostgreSQL database and prove application integrity before declaring recovery ready.

## Procedure

1. Identify the backup ID, checksum, creation time, and retention status.
2. Verify the backup checksum without modifying the source backup.
3. Create an isolated PostgreSQL database using the same schema version.
4. Restore the backup into the isolated database.
5. Run schema and row-count integrity checks.
6. Start the application against the isolated database.
7. Run the smoke tests for identity, journey, evidence, assessment, progression, and reporting.
8. Record results, operator, timestamps, backup ID, and unresolved differences.
9. Destroy the isolated test database only after evidence is stored.

## Pass Criteria

- Backup checksum matches.
- Restore completes without errors.
- Required tables and constraints exist.
- Critical smoke tests pass.
- Restore evidence is attached to the release record.

## Failure Handling

Stop after two failed restore attempts for the same backup. Open a critical challenge, preserve logs, and escalate to the human commander. Do not overwrite the production database during testing.
