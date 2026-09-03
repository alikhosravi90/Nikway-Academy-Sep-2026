-- Additive authorization migration for existing Master System databases.
ALTER TABLE master_definitions
  ADD COLUMN IF NOT EXISTS organization_id TEXT;

CREATE INDEX IF NOT EXISTS master_definitions_organization_idx
  ON master_definitions(organization_id);
