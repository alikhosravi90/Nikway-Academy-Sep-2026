import sys
import re
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


expected = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
actual_paths = set(app.openapi()["paths"])
server_url = (expected.get("servers") or [{}])[0].get("url", "")
prefix = server_url.rstrip("/") if server_url.startswith("/") else ""
expected_paths = {
    f"{prefix}{path}" for path in expected.get("paths", {})
}


def normalize_path(path: str) -> str:
    return re.sub(
        r"\{([A-Za-z0-9]+)\}",
        lambda match: "{" + re.sub(r"([A-Z])", r"_\1", match.group(1)).lower() + "}",
        path,
    )


normalized_actual = {normalize_path(path) for path in actual_paths}
normalized_expected = {normalize_path(path) for path in expected_paths}
missing = sorted(normalized_expected - normalized_actual)
if missing:
    print("missing_paths=" + ",".join(missing))
    raise SystemExit(1)
print(f"contract_paths_ok={len(expected_paths)}")
