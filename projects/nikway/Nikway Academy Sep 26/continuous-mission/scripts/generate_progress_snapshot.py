"""Generate the Release Control Room progress snapshot from readiness evidence."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml


AXIS_ITEMS = {
    "IMPLEMENTATION": {
        "Architecture",
        "Master System Persistence",
        "API",
        "Transactions",
        "Idempotency",
        "Events",
    },
    "RELEASE READINESS": {
        "Database",
        "E2E",
        "Rollback",
        "Evidence",
    },
    "SECURITY": {
        "Security",
        "RLS",
        "Authorization",
        "OIDC",
        "CI Security",
    },
    "OPERATIONS": {
        "Database",
        "Rollback",
        "Operations",
        "E2E",
    },
    "EVIDENCE": {
        "Evidence",
        "Audit",
        "Events",
        "API",
    },
}


def score(status: str) -> int:
    return 100 if status in {"PASS_LOCAL", "PASS_STAGING"} else 0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    matrix_path = root / "readiness-matrix.yaml"
    output_path = (
        root.parent.parent / "frontend" / "src" / "release-readiness.generated.json"
    )
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    items = {
        item["name"]: item
        for item in matrix.get("items", [])
        if isinstance(item, dict) and item.get("name")
    }
    metrics = []
    for axis, names in AXIS_ITEMS.items():
        selected = [items[name] for name in names if name in items]
        verified = round(sum(score(item["status"]) for item in selected) / len(selected))
        metrics.append(
            {
                "name": axis,
                "target": 90,
                "verified": verified,
                "status_counts": {
                    status: sum(item["status"] == status for item in selected)
                    for status in (
                        "PASS_LOCAL",
                        "PASS_STAGING",
                        "BLOCKED_EXTERNAL",
                        "NOT_RUN",
                        "APPROVAL_REQUIRED",
                    )
                    if any(item["status"] == status for item in selected)
                },
                "evidence": [item.get("evidence") for item in selected],
            }
        )
    snapshot = {
        "generated_at": date.today().isoformat(),
        "source": "continuous-mission/readiness-matrix.yaml",
        "release_status": matrix.get("release_status"),
        "production_ready": False,
        "metrics": metrics,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
