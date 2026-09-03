from pathlib import Path

import yaml


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / "publish-ready-sample"
    / ".github"
    / "workflows"
    / "test.yml"
)


def test_ci_workflow_has_required_release_controls():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["python-tests"]["steps"]
    names = {step.get("name") for step in steps if step.get("name")}
    assert "Apply database schema" in names
    assert "Run tests with PostgreSQL" in names
    assert "Verify release state integrity" in names
    assert "Dependency vulnerability scan" in names
    assert "Upload dependency scan evidence" in names
    # `defaults` is job-scoped; PyYAML 5.x may parse YAML 1.1 `on` as True.
    assert (
        workflow["jobs"]["python-tests"]["defaults"]["run"]["working-directory"]
        == "projects/nikway/Nikway Academy Sep 26/continuous-mission/publish-ready-sample/app"
    )
    triggers = workflow.get("on", workflow.get(True))
    assert triggers["push"]["paths"] == [
        "projects/nikway/Nikway Academy Sep 26/continuous-mission/**"
    ]


def test_ci_trivy_fails_on_threshold_findings_and_uploads_report():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["python-tests"]["steps"]
    scan = next(step for step in steps if step.get("name") == "Dependency vulnerability scan")
    upload = next(
        step for step in steps if step.get("name") == "Upload dependency scan evidence"
    )
    assert scan["with"]["exit-code"] == "1"
    assert scan["with"]["severity"] == "CRITICAL,HIGH"
    assert scan["with"]["scan-ref"] == (
        "projects/nikway/Nikway Academy Sep 26/continuous-mission/publish-ready-sample"
    )
    assert upload["with"]["path"] == scan["with"]["output"]
    assert upload["with"]["if-no-files-found"] == "error"
    assert scan["with"]["exit-code"] == "1"


def test_security_workflow_scans_and_uploads_the_publish_ready_sample():
    security_workflow = (
        WORKFLOW.parent / "security-scan.yml"
    ).read_text(encoding="utf-8")
    assert (
        "scan-ref: projects/nikway/Nikway Academy Sep 26/continuous-mission/publish-ready-sample"
        in security_workflow
    )
    assert (
        "path: projects/nikway/Nikway Academy Sep 26/continuous-mission/publish-ready-sample/trivy-fs-report.json"
        in security_workflow
    )
    assert "actions/setup-python@v5" in security_workflow
