# V1 Database Contract

`v1_schema.sql` is the PostgreSQL-only V1 schema. The application must set `app.current_org_id` after OIDC membership resolution inside each request transaction.

The application database role must not be a PostgreSQL superuser or table owner; otherwise it can bypass the intended RLS boundary.

Protected tables also use `FORCE ROW LEVEL SECURITY` so accidental table ownership does not disable the policy. Production still uses a separate least-privilege application role.

Journey-owned records must be checked through module interfaces in application code. Foreign keys provide integrity, while module boundaries provide ownership.
# Database artifacts

`v1_schema.sql` creates the existing NIKWAY V1 schema. The Master System
adapter is additive and is applied by `master_system_schema.sql` after the V1
schema. It creates only `master_definitions` and the append-only
`master_versions` table.

The CI workflow applies both scripts in order. Production/staging migration
execution remains an environment gate and must be evidenced separately.
