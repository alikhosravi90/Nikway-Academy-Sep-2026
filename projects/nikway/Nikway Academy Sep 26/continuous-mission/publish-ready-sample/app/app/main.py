from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.persistence import database_status
from app.auth import resolve_request_membership
from app.master_service import MasterService
from app.master_system import MasterDefinition, MasterSystemError, MasterVersion
from app.repositories import (
    create_assignment as persist_assignment,
    create_assignment_with_trace as persist_assignment_with_trace,
    create_assessment as persist_assessment,
    create_assessment_with_trace as persist_assessment_with_trace,
    create_evidence as persist_evidence,
    create_evidence_with_trace as persist_evidence_with_trace,
    create_journey as persist_journey,
    create_journey_with_trace as persist_journey_with_trace,
    create_organization as persist_organization,
    create_progression as persist_progression,
    create_progression_with_trace as persist_progression_with_trace,
    get_progress_report as read_progress_report,
)
from app.settings import load_settings
from app.storage import S3Storage, plan_upload

app = FastAPI(title="NIKWAY V1 Pilot API", version="0.1.0")
_cors_origins = load_settings().cors_allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Organization-Id", "X-Correlation-Id"],
)
organizations: dict[str, dict] = {}
journeys: dict[str, dict] = {}
assignments: dict[str, dict] = {}
evidence_records: dict[str, dict] = {}
assessments: dict[str, dict] = {}
progression_events: dict[str, dict] = {}
idempotency_results: dict[str, dict] = {}
master_service = MasterService()


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


class OrganizationInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class JourneyInput(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = ""
    steps: list[dict] = Field(min_length=1)


class AssignmentInput(BaseModel):
    learner_id: str


class EvidenceInput(BaseModel):
    step_id: str
    evidence_type: str
    content: str | None = None
    object_storage_ref: str | None = None
    checksum: str | None = None


class AssessmentInput(BaseModel):
    criterion_results: list[dict]
    verdict: str
    comments: str = ""


class InvitationInput(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    role: str = "learner"


class MasterVersionInput(BaseModel):
    version: str = Field(min_length=1, max_length=50)
    schema_definition: dict = Field(default_factory=dict, alias="schema")
    required_fields: tuple[str, ...] = ()
    defaults: dict = Field(default_factory=dict)
    allowed_states: tuple[str, ...] = ()
    overridable_paths: tuple[str, ...] = ()
    extension_paths: tuple[str, ...] = ()
    guidance: tuple[str, ...] = ()


class MasterInput(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    object_type: str = Field(min_length=1, max_length=100)
    current_version: str
    version: MasterVersionInput


def require_key(key: str | None) -> str:
    if not key or len(key) < 8:
        raise HTTPException(400, "Idempotency-Key header is required")
    return key


def require_membership(
    authorization: str | None = Header(None),
) -> dict[str, str] | None:
    settings = load_settings()
    if not settings.require_auth:
        return None
    return resolve_request_membership(
        authorization,
        jwks_url=settings.oidc_jwks_url,
        issuer=settings.oidc_issuer_url,
        audience=settings.oidc_audience,
    )


def require_master_membership(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> dict[str, str]:
    """Master operations always require a verified identity."""
    settings = load_settings()
    if credentials is None:
        raise HTTPException(401, "Bearer token is required")
    return resolve_request_membership(
        f"{credentials.scheme} {credentials.credentials}",
        jwks_url=settings.oidc_jwks_url,
        issuer=settings.oidc_issuer_url,
        audience=settings.oidc_audience,
    )


def _master_definition(payload: MasterInput) -> MasterDefinition:
    version = payload.version
    if version.version != payload.current_version:
        raise HTTPException(422, "current_version must match initial version")
    return MasterDefinition(
        id=payload.id,
        name=payload.name,
        object_type=payload.object_type,
        current_version=payload.current_version,
        versions={
            version.version: MasterVersion(
                version=version.version,
                schema=version.schema_definition,
                required_fields=version.required_fields,
                defaults=version.defaults,
                allowed_states=version.allowed_states,
                overridable_paths=version.overridable_paths,
                extension_paths=version.extension_paths,
                guidance=version.guidance,
            )
        },
        organization_id=None,
    )


def _master_version(payload: MasterVersionInput) -> MasterVersion:
    return MasterVersion(
        version=payload.version,
        schema=payload.schema_definition,
        required_fields=payload.required_fields,
        defaults=payload.defaults,
        allowed_states=payload.allowed_states,
        overridable_paths=payload.overridable_paths,
        extension_paths=payload.extension_paths,
        guidance=payload.guidance,
    )


@app.get("/api/v1/masters")
def list_masters(
    organization_id: str = Header(..., alias="X-Organization-Id"),
    membership: dict[str, str] = Depends(require_master_membership),
) -> list[dict]:
    return master_service.list_masters(membership, organization_id)


@app.get("/api/v1/masters/{master_id}")
def get_master(
    master_id: str,
    organization_id: str = Header(..., alias="X-Organization-Id"),
    membership: dict[str, str] = Depends(require_master_membership),
) -> dict:
    try:
        return master_service.get_master(membership, organization_id, master_id)
    except MasterSystemError as exc:
        raise HTTPException(404, "Master not found") from exc


@app.post("/api/v1/masters", status_code=201)
def create_master(
    payload: MasterInput,
    organization_id: str = Header(..., alias="X-Organization-Id"),
    membership: dict[str, str] = Depends(require_master_membership),
) -> dict:
    try:
        return master_service.create_master(
            membership, organization_id, _master_definition(payload)
        )
    except MasterSystemError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/v1/masters/{master_id}/versions", status_code=201)
def create_master_version(
    master_id: str,
    payload: MasterVersionInput,
    organization_id: str = Header(..., alias="X-Organization-Id"),
    membership: dict[str, str] = Depends(require_master_membership),
) -> dict:
    try:
        return master_service.create_version(
            membership, organization_id, master_id, _master_version(payload)
        )
    except MasterSystemError as exc:
        message = str(exc)
        status = 404 if message.startswith("Unknown master") else 409
        raise HTTPException(status, message) from exc


def make_event(
    verb: str,
    object_id: str,
    object_type: str,
    organization_id: str,
    correlation_id: str | None = None,
) -> dict:
    return {
        "actor": {"id": "demo-user", "type": "system"},
        "verb": verb,
        "object": {"id": object_id, "type": object_type},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {
            "organization_id": organization_id,
            "source_module": object_type.lower(),
            "correlation_id": correlation_id or "local-prototype",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nikway-v1"}


@app.get("/health/dependencies")
def dependency_health() -> dict[str, dict[str, str]]:
    settings = load_settings()
    database = database_status()
    oidc_configured = bool(settings.oidc_issuer_url and settings.oidc_audience)
    storage_configured = bool(settings.s3_endpoint_url)
    return {
        "database": database,
        "oidc": {
            "status": "configured" if oidc_configured else "not_configured",
        },
        "object_storage": {
            "status": "configured" if storage_configured else "not_configured",
        },
    }


@app.get("/health/ready")
def readiness() -> dict:
    settings = load_settings()
    dependencies = dependency_health()
    required = ["database", "oidc", "object_storage"]
    ready = all(
        (
            dependencies["database"]["status"] == "ready"
            if settings.database_required and key == "database"
            else dependencies[key]["status"] == "configured"
        )
        for key in required
    )
    return {
        "status": "ready" if ready else "not_ready",
        "environment": settings.environment,
        "dependencies": dependencies,
    }


@app.post("/api/v1/organizations", status_code=201)
def create_organization(payload: OrganizationInput) -> dict:
    settings = load_settings()
    if settings.database_url and settings.environment in {"staging", "production"}:
        persisted = persist_organization(payload.name)
        if persisted is None:
            raise HTTPException(503, "Database persistence is unavailable")
        return persisted
    organization_id = str(uuid4())
    organizations[organization_id] = {"id": organization_id, "name": payload.name}
    return organizations[organization_id]


@app.post("/api/v1/organizations/{organization_id}/invitations", status_code=202)
def invite_member(
    organization_id: str,
    payload: InvitationInput,
    request_organization_id: str = Header(..., alias="X-Organization-Id"),
    membership: dict | None = Depends(require_membership),
) -> dict:
    if membership and membership["organization_id"] != request_organization_id:
        raise HTTPException(403, "Organization context mismatch")
    if organization_id != request_organization_id:
        raise HTTPException(403, "Organization context mismatch")
    if payload.role not in {"learner", "assessor", "org_admin"}:
        raise HTTPException(422, "Invalid invitation role")
    return {
        "organization_id": organization_id,
        "email": payload.email.lower(),
        "role": payload.role,
        "status": "queued",
    }


@app.post("/api/v1/journeys", status_code=201)
def create_journey(payload: JourneyInput, organization_id: str = Header(..., alias="X-Organization-Id"), membership: dict | None = Depends(require_membership), correlation_id: str | None = Header(None, alias="X-Correlation-Id")) -> dict:
    if membership and membership["organization_id"] != organization_id:
        raise HTTPException(403, "Organization context mismatch")
    settings = load_settings()
    if settings.database_url and settings.environment in {"staging", "production"}:
        persisted = persist_journey_with_trace(
            organization_id, payload.title, payload.description, payload.steps,
            correlation_id or "generated-by-api",
        )
        if persisted is None:
            raise HTTPException(503, "Database persistence is unavailable")
        return persisted
    if organization_id not in organizations:
        raise HTTPException(404, "Organization not found")
    journey_id = str(uuid4())
    journeys[journey_id] = {"id": journey_id, "organization_id": organization_id, **payload.model_dump()}
    return journeys[journey_id]


@app.post("/api/v1/journeys/{journey_id}/assignments", status_code=201)
def assign_journey(
    journey_id: str,
    payload: AssignmentInput,
    organization_id: str = Header(..., alias="X-Organization-Id"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
    membership: dict | None = Depends(require_membership),
) -> dict:
    if membership and membership["organization_id"] != organization_id:
        raise HTTPException(403, "Organization context mismatch")
    key = require_key(idempotency_key)
    if key in idempotency_results:
        return idempotency_results[key]
    settings = load_settings()
    if settings.database_url and settings.environment in {"staging", "production"}:
        persisted = persist_assignment_with_trace(
            organization_id,
            journey_id,
            payload.learner_id,
            correlation_id or "generated-by-api",
        )
        if persisted is None:
            raise HTTPException(503, "Database persistence is unavailable")
        idempotency_results[key] = persisted
        return persisted
    journey = journeys.get(journey_id)
    if not journey or journey["organization_id"] != organization_id:
        raise HTTPException(404, "Journey not found")
    assignment_id = str(uuid4())
    result = {
        "id": assignment_id,
        "journey_id": journey_id,
        "learner_id": payload.learner_id,
        "organization_id": organization_id,
        "status": "active",
        "event": make_event("journey_assigned", assignment_id, "JourneyAssignment", organization_id),
    }
    assignments[assignment_id] = result
    idempotency_results[key] = result
    return result


@app.get("/api/v1/assignments/{assignment_id}")
def get_assignment(assignment_id: str, organization_id: str = Header(..., alias="X-Organization-Id")) -> dict:
    assignment = assignments.get(assignment_id)
    if not assignment or assignment["organization_id"] != organization_id:
        raise HTTPException(404, "Assignment not found")
    return {**assignment, "steps": journeys[assignment["journey_id"]]["steps"]}


@app.post("/api/v1/assignments/{assignment_id}/evidence", status_code=201)
def submit_evidence(
    assignment_id: str,
    payload: EvidenceInput,
    organization_id: str = Header(..., alias="X-Organization-Id"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
    membership: dict | None = Depends(require_membership),
) -> dict:
    if membership and membership["organization_id"] != organization_id:
        raise HTTPException(403, "Organization context mismatch")
    key = require_key(idempotency_key)
    if key in idempotency_results:
        return idempotency_results[key]
    settings = load_settings()
    if settings.database_url and settings.environment in {"staging", "production"}:
        if payload.evidence_type not in {"text", "file", "link"} or not (
            payload.content or payload.object_storage_ref
        ):
            raise HTTPException(422, "Evidence content is required")
        persisted = persist_evidence_with_trace(
            organization_id,
            assignment_id,
            payload.step_id,
            payload.evidence_type,
            payload.content,
            payload.object_storage_ref,
            payload.checksum,
            correlation_id or "generated-by-api",
        )
        if persisted is None:
            raise HTTPException(503, "Database persistence is unavailable")
        idempotency_results[key] = persisted
        return persisted
    assignment = assignments.get(assignment_id)
    if not assignment or assignment["organization_id"] != organization_id:
        raise HTTPException(404, "Assignment not found")
    if payload.evidence_type not in {"text", "file", "link"} or not (payload.content or payload.object_storage_ref):
        raise HTTPException(422, "Evidence content is required")
    evidence_id = str(uuid4())
    result = {
        "id": evidence_id,
        "assignment_id": assignment_id,
        "organization_id": organization_id,
        **payload.model_dump(),
        "status": "submitted",
        "event": make_event("evidence_submitted", evidence_id, "EvidenceRecord", organization_id),
    }
    evidence_records[evidence_id] = result
    idempotency_results[key] = result
    return result


@app.post("/api/v1/assignments/{assignment_id}/evidence/upload", status_code=201)
async def upload_evidence(
    assignment_id: str,
    step_id: str,
    file: UploadFile = File(...),
    organization_id: str = Header(..., alias="X-Organization-Id"),
    membership: dict | None = Depends(require_membership),
) -> dict:
    if membership and membership["organization_id"] != organization_id:
        raise HTTPException(403, "Organization context mismatch")
    content = await file.read()
    plan = plan_upload(
        organization_id,
        assignment_id,
        file.filename or "evidence.bin",
        content,
        file.content_type,
    )
    settings = load_settings()
    if not settings.s3_endpoint_url:
        raise HTTPException(503, "Object storage is not configured")
    try:
        reference = S3Storage(settings.s3_endpoint_url, settings.s3_bucket).put(plan, content)
    except Exception as exc:
        raise HTTPException(503, "Object storage is unavailable") from exc
    return {
        "assignment_id": assignment_id,
        "step_id": step_id,
        "organization_id": organization_id,
        "object_storage_ref": reference,
        "checksum": plan.checksum_sha256,
        "status": "uploaded",
    }


@app.post("/api/v1/evidence/{evidence_id}/assessment", status_code=201)
def assess_evidence(
    evidence_id: str,
    payload: AssessmentInput,
    organization_id: str = Header(..., alias="X-Organization-Id"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
    membership: dict | None = Depends(require_membership),
) -> dict:
    if membership and membership["organization_id"] != organization_id:
        raise HTTPException(403, "Organization context mismatch")
    key = require_key(idempotency_key)
    if key in idempotency_results:
        return idempotency_results[key]
    settings = load_settings()
    if settings.database_url and settings.environment in {"staging", "production"}:
        if payload.verdict not in {"accepted", "needs_revision", "rejected"}:
            raise HTTPException(422, "Invalid verdict")
        persisted = persist_assessment_with_trace(
            organization_id,
            evidence_id,
            payload.criterion_results,
            payload.verdict,
            payload.comments,
            correlation_id or "generated-by-api",
        )
        if persisted is None:
            raise HTTPException(503, "Database persistence is unavailable")
        idempotency_results[key] = persisted
        return persisted
    evidence = evidence_records.get(evidence_id)
    if not evidence or evidence["organization_id"] != organization_id:
        raise HTTPException(404, "Evidence not found")
    if payload.verdict not in {"accepted", "needs_revision", "rejected"}:
        raise HTTPException(422, "Invalid verdict")
    assessment_id = str(uuid4())
    result = {
        "id": assessment_id,
        "evidence_id": evidence_id,
        "organization_id": organization_id,
        **payload.model_dump(),
        "event": make_event("assessment_completed", assessment_id, "AssessmentResult", organization_id),
    }
    assessments[assessment_id] = result
    idempotency_results[key] = result
    return result


@app.post("/api/v1/assessment-results/{assessment_id}/progression", status_code=201)
def decide_progression(
    assessment_id: str,
    organization_id: str = Header(..., alias="X-Organization-Id"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    membership: dict | None = Depends(require_membership),
    correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> dict:
    if membership and membership["organization_id"] != organization_id:
        raise HTTPException(403, "Organization context mismatch")
    key = require_key(idempotency_key)
    if key in idempotency_results:
        return idempotency_results[key]
    settings = load_settings()
    if settings.database_url and settings.environment in {"staging", "production"}:
        persisted = persist_progression_with_trace(
            organization_id, assessment_id, correlation_id or "generated-by-api"
        )
        if persisted is None:
            raise HTTPException(
                409, "Only accepted assessments can progress or persistence is unavailable"
            )
        idempotency_results[key] = persisted
        return persisted
    assessment = assessments.get(assessment_id)
    if not assessment or assessment["organization_id"] != organization_id:
        raise HTTPException(404, "Assessment not found")
    if assessment["verdict"] != "accepted":
        raise HTTPException(409, "Only accepted assessments can progress")
    progression_id = str(uuid4())
    result = {
        "id": progression_id,
        "assessment_id": assessment_id,
        "organization_id": organization_id,
        "status": "advanced",
        "event": make_event("progression_decided", progression_id, "ProgressionEvent", organization_id),
    }
    progression_events[progression_id] = result
    idempotency_results[key] = result
    return result


@app.get("/api/v1/reports/progress")
def progress_report(organization_id: str = Header(..., alias="X-Organization-Id"), membership: dict | None = Depends(require_membership)) -> dict:
    if membership and membership["organization_id"] != organization_id:
        raise HTTPException(403, "Organization context mismatch")
    settings = load_settings()
    if settings.database_url and settings.environment in {"staging", "production"}:
        report = read_progress_report(organization_id)
        if report is None:
            raise HTTPException(503, "Database persistence is unavailable")
        return report
    return {
        "organization_id": organization_id,
        "assignments": len([item for item in assignments.values() if item["organization_id"] == organization_id]),
        "assessments": len([item for item in assessments.values() if item["organization_id"] == organization_id]),
        "progressions": len([item for item in progression_events.values() if item["organization_id"] == organization_id]),
    }
