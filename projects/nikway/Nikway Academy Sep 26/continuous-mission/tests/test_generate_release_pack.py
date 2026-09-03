import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_release_pack.py"
PACK = ROOT / "release-pack" / "NIKWAY-RELEASE-REVIEW-PACK-20260903.json"


def test_release_pack_contains_provenance_and_open_gates():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    assert summary["result"] == "PASS"
    assert pack["production_ready"] is False
    assert pack["files"]
    assert pack["open_gates"]
    assert all("sha256" in item for item in pack["files"].values())
    assert pack["integrity"]["credentials_included"] is False
