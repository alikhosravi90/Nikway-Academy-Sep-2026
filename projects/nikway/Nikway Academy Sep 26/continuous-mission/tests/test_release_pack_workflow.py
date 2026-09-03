from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / "publish-ready-sample"
    / ".github"
    / "workflows"
    / "test.yml"
)


def test_ci_generates_and_uploads_release_review_pack():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Generate release review pack" in workflow
    assert "python scripts/generate_release_pack.py" in workflow
    assert "Upload release review pack" in workflow
    assert "nikway-release-review-pack" in workflow
    assert "if-no-files-found: error" in workflow
