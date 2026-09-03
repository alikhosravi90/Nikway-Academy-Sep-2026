# V1 Migration Policy

Migrations are ordered, immutable, and applied before the application starts serving traffic.

Naming:

```text
NNNN_description.sql
```

Rules:

- Never edit an applied migration.
- Every migration has a checksum in release evidence.
- Destructive changes require an approved migration and rollback decision.
- Production migrations use a role separate from the runtime role.
- Application startup fails closed when schema version is incompatible.
