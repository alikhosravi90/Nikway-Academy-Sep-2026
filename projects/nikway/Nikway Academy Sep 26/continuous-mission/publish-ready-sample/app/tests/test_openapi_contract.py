from app.main import app


def test_openapi_contains_implemented_vertical_slice_paths():
    paths = app.openapi()["paths"]
    expected = {
        "/health",
        "/health/dependencies",
        "/health/ready",
        "/api/v1/organizations",
        "/api/v1/journeys",
        "/api/v1/journeys/{journey_id}/assignments",
        "/api/v1/assignments/{assignment_id}",
        "/api/v1/assignments/{assignment_id}/evidence",
        "/api/v1/evidence/{evidence_id}/assessment",
        "/api/v1/assessment-results/{assessment_id}/progression",
        "/api/v1/reports/progress",
    }
    assert expected.issubset(paths)
