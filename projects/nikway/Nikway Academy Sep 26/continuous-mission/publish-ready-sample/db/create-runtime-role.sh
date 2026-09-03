#!/bin/bash
set -eu

: "${NIKWAY_RUNTIME_PASSWORD:?NIKWAY_RUNTIME_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=runtime_password="$NIKWAY_RUNTIME_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE nikway_runtime LOGIN PASSWORD %L', :'runtime_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nikway_runtime')
\gexec

SELECT format('ALTER ROLE nikway_runtime LOGIN PASSWORD %L', :'runtime_password')
\gexec

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO nikway_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nikway_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nikway_runtime;
ALTER ROLE nikway_runtime NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
SQL
