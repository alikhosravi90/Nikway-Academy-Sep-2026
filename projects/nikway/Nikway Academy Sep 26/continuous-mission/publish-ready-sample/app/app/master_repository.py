"""PostgreSQL adapter for the storage-neutral Master System domain."""

import json

from sqlalchemy import text

from app.master_system import MasterDefinition, MasterSystemError, MasterVersion
from app.persistence import database_engine


def _version_parameters(master_id: str, version: MasterVersion) -> dict:
    return {
        "master_id": master_id,
        "version": version.version,
        "schema_definition": json.dumps(version.schema),
        "required_fields": json.dumps(version.required_fields),
        "defaults": json.dumps(version.defaults),
        "allowed_states": json.dumps(version.allowed_states),
        "overridable_paths": json.dumps(version.overridable_paths),
        "extension_paths": json.dumps(version.extension_paths),
        "guidance": json.dumps(version.guidance),
    }


def persist_master(master: MasterDefinition) -> MasterDefinition | None:
    """Persist a master and its initial version atomically."""
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO master_definitions "
                    "(id, name, object_type, current_version, organization_id) "
                    "VALUES (:id, :name, :object_type, :current_version, :organization_id)"
                ),
                {
                    "id": master.id,
                    "name": master.name,
                    "object_type": master.object_type,
                    "current_version": master.current_version,
                    "organization_id": master.organization_id,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO master_versions "
                    "(master_id, version, schema_definition, required_fields, "
                    "defaults, allowed_states, overridable_paths, extension_paths, guidance) "
                    "VALUES (:master_id, :version, CAST(:schema_definition AS jsonb), "
                    "CAST(:required_fields AS jsonb), CAST(:defaults AS jsonb), "
                    "CAST(:allowed_states AS jsonb), CAST(:overridable_paths AS jsonb), "
                    "CAST(:extension_paths AS jsonb), CAST(:guidance AS jsonb))"
                ),
                _version_parameters(master.id, master.version()),
            )
        return master
    except Exception as exc:
        raise MasterSystemError(f"Unable to persist master: {master.id}") from exc


def retrieve_master(
    master_id: str, organization_id: str | None = None
) -> MasterDefinition | None:
    engine = database_engine()
    if engine is None:
        return None
    with engine.connect() as connection:
        master_row = connection.execute(
            text(
                "SELECT id, name, object_type, current_version, organization_id "
                "FROM master_definitions "
                "WHERE id = :id "
                "AND (CAST(:organization_id AS text) IS NULL "
                "OR organization_id = CAST(:organization_id AS text))"
            ),
            {"id": master_id, "organization_id": organization_id},
        ).mappings().one_or_none()
        if master_row is None:
            return None
        rows = connection.execute(
            text(
                "SELECT version, schema_definition, required_fields, defaults, "
                "allowed_states, overridable_paths, extension_paths, guidance "
                "FROM master_versions WHERE master_id = :master_id ORDER BY version"
            ),
            {"master_id": master_id},
        ).mappings()
        versions = {
            row["version"]: MasterVersion(
                version=row["version"],
                schema=row["schema_definition"],
                required_fields=tuple(row["required_fields"]),
                defaults=row["defaults"],
                allowed_states=tuple(row["allowed_states"]),
                overridable_paths=tuple(row["overridable_paths"]),
                extension_paths=tuple(row["extension_paths"]),
                guidance=tuple(row["guidance"]),
            )
            for row in rows
        }
        return MasterDefinition(
            id=master_row["id"],
            name=master_row["name"],
            object_type=master_row["object_type"],
            current_version=master_row["current_version"],
            versions=versions,
            organization_id=master_row["organization_id"],
        )


def persist_master_version(master_id: str, version: MasterVersion) -> MasterDefinition | None:
    """Append a version and advance the current pointer atomically."""
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM master_definitions WHERE id = :id"),
                {"id": master_id},
            ).scalar()
            if exists is None:
                raise MasterSystemError(f"Unknown master: {master_id}")
            connection.execute(
                text(
                    "INSERT INTO master_versions "
                    "(master_id, version, schema_definition, required_fields, defaults, "
                    "allowed_states, overridable_paths, extension_paths, guidance) "
                    "VALUES (:master_id, :version, CAST(:schema_definition AS jsonb), "
                    "CAST(:required_fields AS jsonb), CAST(:defaults AS jsonb), "
                    "CAST(:allowed_states AS jsonb), CAST(:overridable_paths AS jsonb), "
                    "CAST(:extension_paths AS jsonb), CAST(:guidance AS jsonb))"
                ),
                _version_parameters(master_id, version),
            )
            connection.execute(
                text(
                    "UPDATE master_definitions SET current_version = :version "
                    "WHERE id = :master_id"
                ),
                {"master_id": master_id, "version": version.version},
            )
        return retrieve_master(master_id)
    except MasterSystemError:
        raise
    except Exception as exc:
        raise MasterSystemError(
            f"Unable to persist master version: {master_id}:{version.version}"
        ) from exc
