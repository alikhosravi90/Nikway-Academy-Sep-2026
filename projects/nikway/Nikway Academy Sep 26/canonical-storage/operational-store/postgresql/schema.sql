CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS facts (
  id TEXT PRIMARY KEY,
  statement TEXT NOT NULL,
  domain TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence TEXT,
  owner TEXT,
  source_refs JSONB NOT NULL DEFAULT '[]',
  evidence_refs JSONB NOT NULL DEFAULT '[]',
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  domain TEXT NOT NULL,
  status TEXT NOT NULL,
  context TEXT,
  decision TEXT NOT NULL,
  rationale TEXT,
  consequences JSONB NOT NULL DEFAULT '{}',
  fact_refs JSONB NOT NULL DEFAULT '[]',
  evidence_refs JSONB NOT NULL DEFAULT '[]',
  source_refs JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  external_identity_ref TEXT UNIQUE,
  display_name TEXT NOT NULL,
  role_refs JSONB NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  owner_ref TEXT,
  responsible_ref TEXT,
  reviewer_ref TEXT,
  approver_ref TEXT,
  dependency_refs JSONB NOT NULL DEFAULT '[]',
  definition_of_done JSONB NOT NULL DEFAULT '[]',
  evidence_refs JSONB NOT NULL DEFAULT '[]',
  due_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS releases (
  id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  status TEXT NOT NULL,
  gate_results JSONB NOT NULL DEFAULT '{}',
  deployment_refs JSONB NOT NULL DEFAULT '[]',
  evidence_refs JSONB NOT NULL DEFAULT '[]',
  released_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS audit_events (
  id BIGSERIAL PRIMARY KEY,
  actor_ref TEXT,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  before_state JSONB,
  after_state JSONB,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS semantic_documents (
  id TEXT PRIMARY KEY,
  source_ref TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  embedding vector(1536),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS facts_domain_idx ON facts(domain);
CREATE INDEX IF NOT EXISTS facts_status_idx ON facts(status);
CREATE INDEX IF NOT EXISTS semantic_documents_embedding_idx
  ON semantic_documents USING ivfflat (embedding vector_cosine_ops);
