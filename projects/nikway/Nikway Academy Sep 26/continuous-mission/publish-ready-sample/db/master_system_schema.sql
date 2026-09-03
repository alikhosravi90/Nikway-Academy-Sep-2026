-- NIKWAY Master System persistence adapter.
-- Master versions are append-only: a version row is never updated in place.

CREATE TABLE IF NOT EXISTS master_definitions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  object_type TEXT NOT NULL,
  current_version TEXT NOT NULL,
  organization_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE master_definitions
  ADD COLUMN IF NOT EXISTS organization_id TEXT;

CREATE TABLE IF NOT EXISTS master_versions (
  master_id TEXT NOT NULL REFERENCES master_definitions(id) ON DELETE CASCADE,
  version TEXT NOT NULL,
  schema_definition JSONB NOT NULL,
  required_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  defaults JSONB NOT NULL DEFAULT '{}'::jsonb,
  allowed_states JSONB NOT NULL DEFAULT '[]'::jsonb,
  overridable_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
  extension_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
  guidance JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (master_id, version)
);

CREATE INDEX IF NOT EXISTS master_versions_master_idx
  ON master_versions(master_id, created_at);

COMMENT ON TABLE master_definitions IS
  'Canonical Master System parent definitions.';
COMMENT ON TABLE master_versions IS
  'Immutable, versioned Master System contracts.';
