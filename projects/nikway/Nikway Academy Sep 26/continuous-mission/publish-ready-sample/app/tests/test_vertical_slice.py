from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_vertical_slice_flow():
    organization = client.post("/api/v1/organizations", json={"name": "Pilot Org"}).json()
    headers = {"X-Organization-Id": organization["id"]}
    journey = client.post(
        "/api/v1/journeys",
        headers=headers,
        json={"title": "Systems Thinking", "steps": [{"id": "step-1", "title": "Boundaries"}]},
    ).json()
    assignment = client.post(
        f"/api/v1/journeys/{journey['id']}/assignments",
        headers={**headers, "Idempotency-Key": "assign-001"},
        json={"learner_id": "learner-1"},
    ).json()
    evidence = client.post(
        f"/api/v1/assignments/{assignment['id']}/evidence",
        headers={**headers, "Idempotency-Key": "evidence-001"},
        json={"step_id": "step-1", "evidence_type": "text", "content": "Boundary map"},
    ).json()
    assessment = client.post(
        f"/api/v1/evidence/{evidence['id']}/assessment",
        headers={**headers, "Idempotency-Key": "assessment-001"},
        json={"criterion_results": [{"criterion": "clarity", "accepted": True}], "verdict": "accepted"},
    ).json()
    progression = client.post(
        f"/api/v1/assessment-results/{assessment['id']}/progression",
        headers={**headers, "Idempotency-Key": "progress-001"},
    )
    assert progression.status_code == 201
    assert client.get("/api/v1/reports/progress", headers=headers).json()["progressions"] == 1


def test_assignment_idempotency():
    organization = client.post("/api/v1/organizations", json={"name": "Idempotent Org"}).json()
    headers = {"X-Organization-Id": organization["id"]}
    journey = client.post("/api/v1/journeys", headers=headers, json={"title": "Journey", "steps": [{"id": "s1"}]}).json()
    first = client.post(
        f"/api/v1/journeys/{journey['id']}/assignments",
        headers={**headers, "Idempotency-Key": "same-key-01"},
        json={"learner_id": "learner"},
    ).json()
    second = client.post(
        f"/api/v1/journeys/{journey['id']}/assignments",
        headers={**headers, "Idempotency-Key": "same-key-01"},
        json={"learner_id": "learner"},
    ).json()
    assert first["id"] == second["id"]
