import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lint_security_contract.py"


def test_security_contract_linter_passes_current_contracts():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["result"] == "PASS"
    assert all(report["checks"].values())


def test_security_workflow_runs_contract_linter_before_scan():
    workflow = (
        ROOT
        / "publish-ready-sample"
        / ".github"
        / "workflows"
        / "security-scan.yml"
    ).read_text(encoding="utf-8")
    assert "Validate security contract" in workflow
    assert "python scripts/lint_security_contract.py" in workflow
    assert (
        "working-directory: projects/nikway/Nikway Academy Sep 26/continuous-mission"
        in workflow
    )
