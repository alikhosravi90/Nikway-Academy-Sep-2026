BEGIN;

SELECT set_config('app.current_org_id', '00000000-0000-0000-0000-000000000001', false);

DO $$
DECLARE
  protected_table TEXT;
  visible_count INTEGER;
BEGIN
  FOREACH protected_table IN ARRAY ARRAY[
    'users',
    'memberships',
    'learning_journeys',
    'journey_assignments',
    'evidence_records',
    'assessment_results',
    'progression_events',
    'events',
    'audit_events'
  ]
  LOOP
    EXECUTE format('SELECT count(*) FROM %I WHERE organization_id = $1', protected_table)
      INTO visible_count
      USING '00000000-0000-0000-0000-000000000002'::uuid;
    IF visible_count <> 0 THEN
      RAISE EXCEPTION 'Tenant leak in table %: % rows visible', protected_table, visible_count;
    END IF;
  END LOOP;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO users (organization_id, oidc_subject, email, display_name)
    VALUES ('00000000-0000-0000-0000-000000000002', 'blocked-b-sub', 'blocked@example.test', 'Blocked');
    RAISE EXCEPTION 'Cross-tenant write unexpectedly succeeded';
  EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'Cross-tenant write blocked as expected';
  END;
END $$;

ROLLBACK;
