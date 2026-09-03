import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_progress_snapshot.py"
OUTPUT = ROOT.parent.parent / "frontend" / "src" / "release-readiness.generated.json"


def test_progress_snapshot_is_generated_from_readiness_matrix():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    snapshot = json.loads(result.stdout)
    assert snapshot["source"].endswith("readiness-matrix.yaml")
    assert snapshot["production_ready"] is False
    assert {metric["name"] for metric in snapshot["metrics"]} == {
        "IMPLEMENTATION",
        "RELEASE READINESS",
        "SECURITY",
        "OPERATIONS",
        "EVIDENCE",
    }
    assert OUTPUT.exists()
