# V1 RLS Policy

Every protected request establishes `app.current_org_id` on the active PostgreSQL transaction after OIDC membership resolution.

Protected tables:

`users`, `memberships`, `learning_journeys`, `journey_assignments`, `evidence_records`, `assessment_results`, `progression_events`, `events`, `audit_events`.

Policy requirements:

- Enable RLS on every protected table.
- Permit reads and writes only when `organization_id = current_setting('app.current_org_id')`.
- Use a non-superuser application database role.
- Reset organization context when a connection returns to the pool.
- Test both read and write isolation with Organization A and Organization B.

The application `WHERE organization_id = ...` filter is useful but is not the security boundary; PostgreSQL RLS is the backstop.
