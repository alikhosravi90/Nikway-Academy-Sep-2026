# RLS Test Plan

Use two organizations, A and B, with one user and one complete journey assignment in each.

For each protected table:

1. Set `app.current_org_id` to A.
2. Assert A can read and write only A rows.
3. Assert A cannot read B rows.
4. Assert inserting or updating a B `organization_id` fails.
5. Repeat with B.

The test passes only when all protected tables satisfy both read and write isolation.

The schema must use `FORCE ROW LEVEL SECURITY`; tests run with a least-privilege role, never a PostgreSQL superuser.
