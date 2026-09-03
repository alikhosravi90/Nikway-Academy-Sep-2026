import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_release_state.py"


def test_release_state_verifier_accepts_current_matrix():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["result"] == "PASS"
    assert summary["items"] == 18
    assert summary["production_ready"] is False


def test_release_state_verifier_rejects_missing_evidence(tmp_path):
    matrix = {
        "release_status": "WAITING_FOR_EXTERNAL_ENVIRONMENT_INPUT",
        "items": [
            {
                "name": "Missing",
                "status": "PASS_LOCAL",
                "evidence": "evidence/missing.yaml",
            },
            {
                "name": "Open",
                "status": "BLOCKED_EXTERNAL",
                "evidence": None,
            },
        ],
    }
    (tmp_path / "readiness-matrix.yaml").write_text(
        yaml.safe_dump(matrix), encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--mission-root", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "missing evidence references" in result.stderr
