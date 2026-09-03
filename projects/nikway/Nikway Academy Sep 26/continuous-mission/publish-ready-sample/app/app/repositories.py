from collections.abc import Iterator
from contextlib import contextmanager
import json

from sqlalchemy.engine import Connection
from sqlalchemy import text

from app.persistence import database_engine, set_organization_context


def _insert_trace(
    connection,
    organization_id: str,
    verb: str,
    object_payload: dict,
    action: str,
    entity_type: str,
    entity_id: str,
    before_state: dict | None,
    after_state: dict | None,
    context: dict,
) -> None:
    connection.execute(
        text(
            "INSERT INTO events (organization_id, actor, verb, object, context) "
            "VALUES (:organization_id, CAST(:actor AS jsonb), :verb, "
            "CAST(:object_payload AS jsonb), CAST(:context AS jsonb))"
        ),
        {
            "organization_id": organization_id,
            "actor": json.dumps({"id": "system", "type": "system"}),
            "verb": verb,
            "object_payload": json.dumps(object_payload),
            "context": json.dumps(context),
        },
    )
    connection.execute(
        text(
            "INSERT INTO audit_events "
            "(organization_id, action, entity_type, entity_id, before_state, after_state) "
            "VALUES (:organization_id, :action, :entity_type, :entity_id, "
            "CAST(:before_state AS jsonb), CAST(:after_state AS jsonb))"
        ),
        {
            "organization_id": organization_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before_state": json.dumps(before_state) if before_state else None,
            "after_state": json.dumps(after_state) if after_state else None,
        },
    )


@contextmanager
def organization_transaction(organization_id: str) -> Iterator[Connection]:
    """Open a transaction with the tenant context required by PostgreSQL RLS."""
    engine = database_engine()
    if engine is None:
        raise RuntimeError("DATABASE_URL is required for a database transaction")
    with engine.begin() as connection:
        set_organization_context(connection, organization_id)
        yield connection


class RepositoryBoundary:
    """Small seam for replacing in-memory stores with SQL repositories."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id

    def transaction(self) -> Iterator[Connection]:
        return organization_transaction(self.organization_id)


def create_organization(name: str) -> dict | None:
    """Persist an organization when PostgreSQL mode is explicitly enabled."""
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            row = connection.execute(
                text(
                    "INSERT INTO organizations (name) VALUES (:name) "
                    "RETURNING id::text AS id, name"
                ),
                {"name": name},
            ).mappings().one()
            return dict(row)
    except Exception:
        return None


def create_journey(
    organization_id: str, title: str, description: str, steps: list[dict]
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            journey = connection.execute(
                text(
                    "INSERT INTO learning_journeys "
                    "(organization_id, title, description) "
                    "VALUES (:organization_id, :title, :description) "
                    "RETURNING id::text AS id, organization_id::text AS organization_id, "
                    "title, description"
                ),
                {
                    "organization_id": organization_id,
                    "title": title,
                    "description": description,
                },
            ).mappings().one()
            journey_id = journey["id"]
            for position, step in enumerate(steps, start=1):
                connection.execute(
                    text(
                        "INSERT INTO journey_steps "
                        "(journey_id, position, title, content_ref, criteria) "
                        "VALUES (:journey_id, :position, :title, :content_ref, "
                        "CAST(:criteria AS jsonb))"
                    ),
                    {
                        "journey_id": journey_id,
                        "position": position,
                        "title": step.get("title", f"Step {position}"),
                        "content_ref": step.get("content_ref"),
                        "criteria": "[]",
                    },
                )
            return {**dict(journey), "steps": steps}
    except Exception:
        return None


def create_journey_with_trace(
    organization_id: str,
    title: str,
    description: str,
    steps: list[dict],
    correlation_id: str,
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            journey = connection.execute(
                text(
                    "INSERT INTO learning_journeys "
                    "(organization_id, title, description) VALUES "
                    "(:organization_id, :title, :description) "
                    "RETURNING id::text AS id, organization_id::text AS organization_id, "
                    "title, description"
                ),
                {"organization_id": organization_id, "title": title, "description": description},
            ).mappings().one()
            for position, step in enumerate(steps, start=1):
                connection.execute(
                    text(
                        "INSERT INTO journey_steps "
                        "(journey_id, position, title, content_ref, criteria) "
                        "VALUES (:journey_id, :position, :title, :content_ref, "
                        "CAST(:criteria AS jsonb))"
                    ),
                    {
                        "journey_id": journey["id"],
                        "position": position,
                        "title": step.get("title", f"Step {position}"),
                        "content_ref": step.get("content_ref"),
                        "criteria": "[]",
                    },
                )
            context = {
                "organization_id": organization_id,
                "correlation_id": correlation_id,
                "source_module": "journey",
            }
            _insert_trace(
                connection, organization_id, "journey_created",
                {"id": journey["id"], "type": "LearningJourney"},
                "created", "LearningJourney", journey["id"], None,
                {**dict(journey), "steps": steps, **context}, context,
            )
            return {**dict(journey), "steps": steps}
    except Exception:
        return None


def create_assignment(
    organization_id: str, journey_id: str, learner_id: str
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            row = connection.execute(
                text(
                    "INSERT INTO journey_assignments "
                    "(organization_id, journey_id, learner_id) "
                    "VALUES (:organization_id, :journey_id, :learner_id) "
                    "RETURNING id::text AS id, journey_id::text AS journey_id, "
                    "learner_id::text AS learner_id, "
                    "organization_id::text AS organization_id, status"
                ),
                {
                    "organization_id": organization_id,
                    "journey_id": journey_id,
                    "learner_id": learner_id,
                },
            ).mappings().one()
            result = dict(row)
            result["event"] = {
                "actor": {"id": "system", "type": "system"},
                "verb": "journey_assigned",
                "object": {"id": result["id"], "type": "JourneyAssignment"},
                "context": {"organization_id": organization_id},
            }
            return result
    except Exception:
        return None


def create_assignment_with_trace(
    organization_id: str,
    journey_id: str,
    learner_id: str,
    correlation_id: str,
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            row = connection.execute(
                text(
                    "INSERT INTO journey_assignments "
                    "(organization_id, journey_id, learner_id) "
                    "VALUES (:organization_id, :journey_id, :learner_id) "
                    "RETURNING id::text AS id, journey_id::text AS journey_id, "
                    "learner_id::text AS learner_id, organization_id::text AS organization_id, status"
                ),
                {
                    "organization_id": organization_id,
                    "journey_id": journey_id,
                    "learner_id": learner_id,
                },
            ).mappings().one()
            result = dict(row)
            event_context = {
                "organization_id": organization_id,
                "correlation_id": correlation_id,
                "source_module": "journey_assignment",
            }
            connection.execute(
                text(
                    "INSERT INTO events (organization_id, actor, verb, object, context) "
                    "VALUES (:organization_id, CAST(:actor AS jsonb), :verb, "
                    "CAST(:object_payload AS jsonb), CAST(:context AS jsonb))"
                ),
                {
                    "organization_id": organization_id,
                    "actor": json.dumps({"id": "system", "type": "system"}),
                    "verb": "journey_assigned",
                    "object_payload": json.dumps(
                        {"id": result["id"], "type": "JourneyAssignment"}
                    ),
                    "context": json.dumps(event_context),
                },
            )
            connection.execute(
                text(
                    "INSERT INTO audit_events "
                    "(organization_id, action, entity_type, entity_id, after_state) "
                    "VALUES (:organization_id, :action, :entity_type, :entity_id, "
                    "CAST(:after_state AS jsonb))"
                ),
                {
                    "organization_id": organization_id,
                    "action": "created",
                    "entity_type": "JourneyAssignment",
                    "entity_id": result["id"],
                    "after_state": json.dumps(
                        {**result, "correlation_id": correlation_id}
                    ),
                },
            )
            result["event"] = {
                "verb": "journey_assigned",
                "context": event_context,
            }
            return result
    except Exception:
        return None


def create_evidence(
    organization_id: str,
    assignment_id: str,
    step_id: str,
    evidence_type: str,
    content: str | None,
    object_storage_ref: str | None,
    checksum: str | None,
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            row = connection.execute(
                text(
                    "INSERT INTO evidence_records "
                    "(organization_id, assignment_id, step_id, submitted_by, "
                    "evidence_type, content, object_storage_ref, checksum) "
                    "VALUES (:organization_id, :assignment_id, :step_id, "
                    "CAST(:submitted_by AS uuid), :evidence_type, :content, "
                    ":object_storage_ref, :checksum) "
                    "RETURNING id::text AS id, assignment_id::text AS assignment_id, "
                    "organization_id::text AS organization_id, evidence_type, "
                    "content, object_storage_ref, checksum, status"
                ),
                {
                    "organization_id": organization_id,
                    "assignment_id": assignment_id,
                    "step_id": step_id,
                    "submitted_by": "00000000-0000-0000-0000-000000000001",
                    "evidence_type": evidence_type,
                    "content": content,
                    "object_storage_ref": object_storage_ref,
                    "checksum": checksum,
                },
            ).mappings().one()
            result = dict(row)
            result["event"] = {
                "actor": {"id": "system", "type": "system"},
                "verb": "evidence_submitted",
                "object": {"id": result["id"], "type": "EvidenceRecord"},
                "context": {"organization_id": organization_id},
            }
            return result
    except Exception:
        return None


def create_evidence_with_trace(
    organization_id: str, assignment_id: str, step_id: str,
    evidence_type: str, content: str | None, object_storage_ref: str | None,
    checksum: str | None, correlation_id: str,
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            row = connection.execute(
                text(
                    "INSERT INTO evidence_records "
                    "(organization_id, assignment_id, step_id, submitted_by, "
                    "evidence_type, content, object_storage_ref, checksum) "
                    "VALUES (:organization_id, :assignment_id, :step_id, "
                    "CAST(:submitted_by AS uuid), :evidence_type, :content, "
                    ":object_storage_ref, :checksum) "
                    "RETURNING id::text AS id, assignment_id::text AS assignment_id, "
                    "organization_id::text AS organization_id, evidence_type, content, "
                    "object_storage_ref, checksum, status"
                ),
                {
                    "organization_id": organization_id, "assignment_id": assignment_id,
                    "step_id": step_id,
                    "submitted_by": "00000000-0000-0000-0000-000000000001",
                    "evidence_type": evidence_type, "content": content,
                    "object_storage_ref": object_storage_ref, "checksum": checksum,
                },
            ).mappings().one()
            result = dict(row)
            context = {
                "organization_id": organization_id,
                "correlation_id": correlation_id,
                "source_module": "evidence",
            }
            _insert_trace(
                connection, organization_id, "evidence_submitted",
                {"id": result["id"], "type": "EvidenceRecord"},
                "created", "EvidenceRecord", result["id"], None,
                {**result, **context}, context,
            )
            result["event"] = {"verb": "evidence_submitted", "context": context}
            return result
    except Exception:
        return None


def create_assessment(
    organization_id: str,
    evidence_id: str,
    criterion_results: list[dict],
    verdict: str,
    comments: str,
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            row = connection.execute(
                text(
                    "INSERT INTO assessment_results "
                    "(organization_id, evidence_id, assessor_id, criterion_results, "
                    "verdict, comments) "
                    "VALUES (:organization_id, :evidence_id, "
                    "CAST(:assessor_id AS uuid), CAST(:criterion_results AS jsonb), "
                    ":verdict, :comments) "
                    "RETURNING id::text AS id, evidence_id::text AS evidence_id, "
                    "organization_id::text AS organization_id, criterion_results, "
                    "verdict, comments"
                ),
                {
                    "organization_id": organization_id,
                    "evidence_id": evidence_id,
                    "assessor_id": "00000000-0000-0000-0000-000000000001",
                    "criterion_results": __import__("json").dumps(criterion_results),
                    "verdict": verdict,
                    "comments": comments,
                },
            ).mappings().one()
            result = dict(row)
            result["event"] = {
                "actor": {"id": "system", "type": "system"},
                "verb": "assessment_completed",
                "object": {"id": result["id"], "type": "AssessmentResult"},
                "context": {"organization_id": organization_id},
            }
            return result
    except Exception:
        return None


def create_assessment_with_trace(
    organization_id: str, evidence_id: str, criterion_results: list[dict],
    verdict: str, comments: str, correlation_id: str,
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            row = connection.execute(
                text(
                    "INSERT INTO assessment_results "
                    "(organization_id, evidence_id, assessor_id, criterion_results, "
                    "verdict, comments) VALUES (:organization_id, :evidence_id, "
                    "CAST(:assessor_id AS uuid), CAST(:criterion_results AS jsonb), "
                    ":verdict, :comments) RETURNING id::text AS id, "
                    "evidence_id::text AS evidence_id, organization_id::text AS "
                    "organization_id, criterion_results, verdict, comments"
                ),
                {
                    "organization_id": organization_id, "evidence_id": evidence_id,
                    "assessor_id": "00000000-0000-0000-0000-000000000001",
                    "criterion_results": json.dumps(criterion_results),
                    "verdict": verdict, "comments": comments,
                },
            ).mappings().one()
            result = dict(row)
            context = {
                "organization_id": organization_id,
                "correlation_id": correlation_id,
                "source_module": "assessment",
            }
            _insert_trace(
                connection, organization_id, "assessment_completed",
                {"id": result["id"], "type": "AssessmentResult"},
                "created", "AssessmentResult", result["id"], None,
                {**result, **context}, context,
            )
            result["event"] = {"verb": "assessment_completed", "context": context}
            return result
    except Exception:
        return None


def create_progression(
    organization_id: str, assessment_id: str
) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            assessment = connection.execute(
                text(
                    "SELECT id::text AS id, evidence_id::text AS evidence_id, verdict "
                    "FROM assessment_results WHERE id = :assessment_id"
                ),
                {"assessment_id": assessment_id},
            ).mappings().one_or_none()
            if not assessment or assessment["verdict"] != "accepted":
                return None
            assignment_id = connection.execute(
                text(
                    "SELECT assignment_id::text FROM evidence_records "
                    "WHERE id = :evidence_id"
                ),
                {"evidence_id": assessment["evidence_id"]},
            ).scalar_one()
            row = connection.execute(
                text(
                    "INSERT INTO progression_events "
                    "(organization_id, assignment_id, assessment_id, reason) "
                    "VALUES (:organization_id, :assignment_id, :assessment_id, "
                    "        'assessment accepted') "
                    "RETURNING id::text AS id, assignment_id::text AS assignment_id, "
                    "assessment_id::text AS assessment_id, "
                    "organization_id::text AS organization_id, reason"
                ),
                {
                    "organization_id": organization_id,
                    "assignment_id": assignment_id,
                    "assessment_id": assessment_id,
                },
            ).mappings().one()
            result = {**dict(row), "status": "advanced"}
            result["event"] = {
                "actor": {"id": "system", "type": "system"},
                "verb": "progression_decided",
                "object": {"id": result["id"], "type": "ProgressionEvent"},
                "context": {"organization_id": organization_id},
            }
            return result
    except Exception:
        return None


def create_progression_with_trace(
    organization_id: str, assessment_id: str, correlation_id: str
) -> dict | None:
    """Create progression, event, and audit record in one tenant-scoped transaction."""
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            assessment = connection.execute(
                text(
                    "SELECT id::text AS id, evidence_id::text AS evidence_id, verdict "
                    "FROM assessment_results WHERE id = :assessment_id"
                ),
                {"assessment_id": assessment_id},
            ).mappings().one_or_none()
            if not assessment or assessment["verdict"] != "accepted":
                return None
            assignment_id = connection.execute(
                text(
                    "SELECT assignment_id::text FROM evidence_records "
                    "WHERE id = :evidence_id"
                ),
                {"evidence_id": assessment["evidence_id"]},
            ).scalar_one()
            row = connection.execute(
                text(
                    "INSERT INTO progression_events "
                    "(organization_id, assignment_id, assessment_id, reason) "
                    "VALUES (:organization_id, :assignment_id, :assessment_id, "
                    ":reason) "
                    "RETURNING id::text AS id, assignment_id::text AS assignment_id, "
                    "assessment_id::text AS assessment_id, "
                    "organization_id::text AS organization_id, reason"
                ),
                {
                    "organization_id": organization_id,
                    "assignment_id": assignment_id,
                    "assessment_id": assessment_id,
                    "reason": "assessment accepted",
                },
            ).mappings().one()
            result = {**dict(row), "status": "advanced"}
            context = {
                "organization_id": organization_id,
                "correlation_id": correlation_id,
                "source_module": "progression",
            }
            connection.execute(
                text(
                    "INSERT INTO events (organization_id, actor, verb, object, context) "
                    "VALUES (:organization_id, CAST(:actor AS jsonb), :verb, "
                    "CAST(:object_payload AS jsonb), CAST(:context AS jsonb))"
                ),
                {
                    "organization_id": organization_id,
                    "actor": json.dumps({"id": "system", "type": "system"}),
                    "verb": "progression_decided",
                    "object_payload": json.dumps(
                        {"id": result["id"], "type": "ProgressionEvent"}
                    ),
                    "context": json.dumps(context),
                },
            )
            connection.execute(
                text(
                    "INSERT INTO audit_events "
                    "(organization_id, action, entity_type, entity_id, after_state) "
                    "VALUES (:organization_id, :action, :entity_type, :entity_id, "
                    "CAST(:after_state AS jsonb))"
                ),
                {
                    "organization_id": organization_id,
                    "action": "created",
                    "entity_type": "ProgressionEvent",
                    "entity_id": result["id"],
                    "after_state": json.dumps({**result, **context}),
                },
            )
            result["event"] = {"verb": "progression_decided", "context": context}
            return result
    except Exception:
        return None


def get_progress_report(organization_id: str) -> dict | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            counts = connection.execute(
                text(
                    "SELECT "
                    "(SELECT count(*) FROM journey_assignments "
                    " WHERE organization_id = :organization_id) AS assignments, "
                    "(SELECT count(*) FROM assessment_results "
                    " WHERE organization_id = :organization_id) AS assessments, "
                    "(SELECT count(*) FROM progression_events "
                    " WHERE organization_id = :organization_id) AS progressions"
                ),
                {"organization_id": organization_id},
            ).mappings().one()
            return {
                "organization_id": organization_id,
                "assignments": int(counts["assignments"]),
                "assessments": int(counts["assessments"]),
                "progressions": int(counts["progressions"]),
            }
    except Exception:
        return None


def record_event(
    organization_id: str,
    actor: dict,
    verb: str,
    object_payload: dict,
    context: dict,
) -> str | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            event_id = connection.execute(
                text(
                    "INSERT INTO events "
                    "(organization_id, actor, verb, object, context) "
                    "VALUES (:organization_id, CAST(:actor AS jsonb), :verb, "
                    "CAST(:object_payload AS jsonb), CAST(:context AS jsonb)) "
                    "RETURNING id::text"
                ),
                {
                    "organization_id": organization_id,
                    "actor": json.dumps(actor),
                    "verb": verb,
                    "object_payload": json.dumps(object_payload),
                    "context": json.dumps(context),
                },
            ).scalar_one()
            return str(event_id)
    except Exception:
        return None


def record_trace(
    organization_id: str,
    correlation_id: str,
    actor: dict,
    action: str,
    entity_type: str,
    entity_id: str,
    before_state: dict | None,
    after_state: dict | None,
    verb: str,
    object_payload: dict,
    context: dict,
) -> tuple[str, int] | None:
    """Persist event and audit data in one tenant-scoped transaction."""
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            event_id = connection.execute(
                text(
                    "INSERT INTO events "
                    "(organization_id, actor, verb, object, context) "
                    "VALUES (:organization_id, CAST(:actor AS jsonb), :verb, "
                    "CAST(:object_payload AS jsonb), CAST(:context AS jsonb)) "
                    "RETURNING id::text"
                ),
                {
                    "organization_id": organization_id,
                    "actor": json.dumps(actor),
                    "verb": verb,
                    "object_payload": json.dumps(object_payload),
                    "context": json.dumps({**context, "correlation_id": correlation_id}),
                },
            ).scalar_one()
            audit_id = connection.execute(
                text(
                    "INSERT INTO audit_events "
                    "(organization_id, action, entity_type, entity_id, "
                    "before_state, after_state) "
                    "VALUES (:organization_id, :action, :entity_type, :entity_id, "
                    "CAST(:before_state AS jsonb), CAST(:after_state AS jsonb)) "
                    "RETURNING id"
                ),
                {
                    "organization_id": organization_id,
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "before_state": json.dumps(before_state) if before_state else None,
                    "after_state": json.dumps(after_state) if after_state else None,
                },
            ).scalar_one()
            return str(event_id), int(audit_id)
    except Exception:
        return None


def record_audit_event(
    organization_id: str,
    actor_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    before_state: dict | None,
    after_state: dict | None,
) -> int | None:
    engine = database_engine()
    if engine is None:
        return None
    try:
        with engine.begin() as connection:
            set_organization_context(connection, organization_id)
            audit_id = connection.execute(
                text(
                    "INSERT INTO audit_events "
                    "(organization_id, actor_id, action, entity_type, entity_id, "
                    "before_state, after_state) "
                    "VALUES (:organization_id, CAST(:actor_id AS uuid), :action, "
                    ":entity_type, :entity_id, CAST(:before_state AS jsonb), "
                    "CAST(:after_state AS jsonb)) RETURNING id"
                ),
                {
                    "organization_id": organization_id,
                    "actor_id": actor_id,
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "before_state": json.dumps(before_state) if before_state else None,
                    "after_state": json.dumps(after_state) if after_state else None,
                },
            ).scalar_one()
            return int(audit_id)
    except Exception:
        return None
