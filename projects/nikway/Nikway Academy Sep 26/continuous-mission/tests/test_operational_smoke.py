import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "operational_smoke.py"


def test_operational_smoke_script_is_runnable():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--api",
            "http://127.0.0.1:9",
            "--oidc",
            "http://127.0.0.1:9/realm",
            "--minio",
            "http://127.0.0.1:9",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    checks = json.loads(result.stdout)
    assert checks["api_health"]["status"] == "UNREACHABLE_LOCAL"
    assert checks["oidc_discovery"]["status"] == "UNREACHABLE_LOCAL"
    assert checks["minio_health"]["status"] == "UNREACHABLE_LOCAL"
