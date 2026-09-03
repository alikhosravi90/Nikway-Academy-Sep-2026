CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  oidc_subject TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL,
  display_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  user_id UUID NOT NULL REFERENCES users(id),
  role TEXT NOT NULL CHECK (role IN ('learner', 'assessor', 'org_admin', 'nikway_admin')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (organization_id, user_id, role)
);

CREATE TABLE invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  email TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('learner', 'assessor', 'org_admin')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'revoked')),
  invited_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (organization_id, email)
);

CREATE TABLE learning_journeys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE journey_steps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  journey_id UUID NOT NULL REFERENCES learning_journeys(id) ON DELETE CASCADE,
  position INTEGER NOT NULL CHECK (position > 0),
  title TEXT NOT NULL,
  content_ref TEXT,
  criteria JSONB NOT NULL DEFAULT '[]',
  UNIQUE (journey_id, position)
);

CREATE TABLE journey_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  journey_id UUID NOT NULL REFERENCES learning_journeys(id),
  learner_id UUID NOT NULL REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (journey_id, learner_id)
);

CREATE TABLE evidence_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  assignment_id UUID NOT NULL REFERENCES journey_assignments(id),
  step_id UUID NOT NULL REFERENCES journey_steps(id),
  submitted_by UUID NOT NULL REFERENCES users(id),
  evidence_type TEXT NOT NULL CHECK (evidence_type IN ('text', 'file', 'link')),
  content TEXT,
  object_storage_ref TEXT,
  checksum TEXT,
  status TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'under_review', 'accepted', 'needs_revision', 'rejected')),
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (content IS NOT NULL OR object_storage_ref IS NOT NULL)
);

CREATE TABLE assessment_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  evidence_id UUID NOT NULL REFERENCES evidence_records(id),
  assessor_id UUID NOT NULL REFERENCES users(id),
  criterion_results JSONB NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('accepted', 'needs_revision', 'rejected')),
  comments TEXT NOT NULL DEFAULT '',
  assessed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE progression_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  assignment_id UUID NOT NULL REFERENCES journey_assignments(id),
  assessment_id UUID NOT NULL REFERENCES assessment_results(id),
  previous_step_id UUID REFERENCES journey_steps(id),
  next_step_id UUID REFERENCES journey_steps(id),
  reason TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (assessment_id)
);

CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  actor JSONB NOT NULL,
  verb TEXT NOT NULL,
  object JSONB NOT NULL,
  context JSONB NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id BIGSERIAL PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id),
  actor_id UUID,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  before_state JSONB,
  after_state JSONB,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX evidence_assignment_idx ON evidence_records(assignment_id);
CREATE INDEX assessment_evidence_idx ON assessment_results(evidence_id);
CREATE INDEX events_organization_time_idx ON events(organization_id, occurred_at);
CREATE INDEX audit_organization_time_idx ON audit_events(organization_id, occurred_at);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_journeys ENABLE ROW LEVEL SECURITY;
ALTER TABLE journey_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE progression_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE memberships FORCE ROW LEVEL SECURITY;
ALTER TABLE invitations FORCE ROW LEVEL SECURITY;
ALTER TABLE learning_journeys FORCE ROW LEVEL SECURITY;
ALTER TABLE journey_assignments FORCE ROW LEVEL SECURITY;
ALTER TABLE evidence_records FORCE ROW LEVEL SECURITY;
ALTER TABLE assessment_results FORCE ROW LEVEL SECURITY;
ALTER TABLE progression_events FORCE ROW LEVEL SECURITY;
ALTER TABLE events FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;

CREATE POLICY users_tenant_policy ON users
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY memberships_tenant_policy ON memberships
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY invitations_tenant_policy ON invitations
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY journeys_tenant_policy ON learning_journeys
  USING (organization_id IS NULL OR organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id IS NULL OR organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY assignments_tenant_policy ON journey_assignments
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY evidence_tenant_policy ON evidence_records
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY assessments_tenant_policy ON assessment_results
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY progression_tenant_policy ON progression_events
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY events_tenant_policy ON events
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
CREATE POLICY audit_tenant_policy ON audit_events
  USING (organization_id::text = current_setting('app.current_org_id', true))
  WITH CHECK (organization_id::text = current_setting('app.current_org_id', true));
