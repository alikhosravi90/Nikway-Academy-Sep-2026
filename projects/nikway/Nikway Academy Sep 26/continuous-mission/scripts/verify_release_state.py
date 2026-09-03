"""Deterministic integrity checks for the NIKWAY release state.

This verifier checks references and gate semantics only. It does not promote
the release and it never turns an external dependency into a local pass.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


ALLOWED_STATUSES = {
    "PASS_LOCAL",
    "PASS_STAGING",
    "BLOCKED_EXTERNAL",
    "NOT_RUN",
    "APPROVAL_REQUIRED",
}


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a YAML object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mission-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    root = args.mission_root.resolve()
    matrix_path = root / "readiness-matrix.yaml"
    matrix = load_yaml(matrix_path)

    items = matrix.get("items")
    if not isinstance(items, list) or not items:
        raise AssertionError("readiness matrix has no items")

    missing_refs: list[str] = []
    invalid_statuses: list[str] = []
    for item in items:
        name = str(item.get("name", "<unnamed>"))
        status = item.get("status")
        if status not in ALLOWED_STATUSES:
            invalid_statuses.append(f"{name}={status}")
        evidence = item.get("evidence")
        if evidence:
            evidence_path = root / str(evidence)
            if not evidence_path.exists():
                missing_refs.append(f"{name}: {evidence}")

    if invalid_statuses:
        raise AssertionError("invalid statuses: " + ", ".join(invalid_statuses))
    if missing_refs:
        raise AssertionError("missing evidence references: " + ", ".join(missing_refs))

    release_status = matrix.get("release_status")
    if release_status not in {"WAITING_FOR_EXTERNAL_ENVIRONMENT_INPUT", "APPROVAL_REQUIRED"}:
        raise AssertionError(f"unsafe release status: {release_status}")

    blocked = [
        item["name"]
        for item in items
        if item.get("status") in {"BLOCKED_EXTERNAL", "NOT_RUN"}
    ]
    if not blocked:
        raise AssertionError("external/unevaluated gates must be explicit")

    summary = {
        "result": "PASS",
        "items": len(items),
        "evidence_references_checked": len(items),
        "blocked_or_not_run": blocked,
        "release_status": release_status,
        "production_ready": False,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
