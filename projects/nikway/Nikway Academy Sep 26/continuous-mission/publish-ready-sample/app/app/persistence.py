import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def database_engine() -> Engine | None:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        return None
    try:
        return create_engine(database_url, pool_pre_ping=True, pool_recycle=300)
    except Exception:
        return None


def set_organization_context(connection, organization_id: str) -> None:
    """Set the transaction-local tenant used by PostgreSQL RLS policies."""
    connection.execute(
        text("SELECT set_config('app.current_org_id', :organization_id, true)"),
        {"organization_id": organization_id},
    )


def database_status() -> dict[str, str]:
    engine = database_engine()
    if engine is None:
        return {"mode": "in_memory", "status": "not_configured"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"mode": "postgresql", "status": "ready"}
    except Exception:
        return {"mode": "postgresql", "status": "unavailable"}
