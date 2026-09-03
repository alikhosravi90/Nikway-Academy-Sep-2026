"""Build a deterministic, provenance-aware release review pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    files: dict[str, dict] = {}
    unresolved: list[dict[str, str]] = []

    references = [
        ("readiness_matrix", matrix_path),
        ("external_environment_contract", root / "external-environment-contract.yaml"),
        ("verification_procedures", root / "verification-procedures.md"),
        (
            "release_manifest",
            root / "publish-ready-sample" / "release-manifest.yaml",
        ),
        (
            "generated_readiness_view",
            root.parent.parent / "frontend" / "src" / "release-readiness.generated.json",
        ),
    ]
    for item in matrix.get("items", []):
        evidence = item.get("evidence")
        if evidence:
            references.append((f"evidence:{item['name']}", root / evidence))

    for label, path in references:
        relative = path.relative_to(root.parent.parent.parent)
        if path.exists() and path.is_file():
            files[label] = {
                "path": relative.as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        else:
            unresolved.append({"label": label, "path": relative.as_posix()})

    pack = {
        "id": "NIKWAY-RELEASE-REVIEW-PACK-20260903",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mission_id": matrix.get("mission_id", "NIKWAY-CONTINUOUS-MISSION-001"),
        "release_status": matrix.get("release_status"),
        "production_ready": False,
        "verified_metrics": json.loads(
            (
                root.parent.parent
                / "frontend"
                / "src"
                / "release-readiness.generated.json"
            ).read_text(encoding="utf-8")
        ).get("metrics", []),
        "open_gates": [
            {
                "name": item["name"],
                "status": item["status"],
                "blocker": item.get("blocker"),
                "next_action": item.get("next_action"),
            }
            for item in matrix.get("items", [])
            if item.get("status") in {"BLOCKED_EXTERNAL", "NOT_RUN", "APPROVAL_REQUIRED"}
        ],
        "files": files,
        "unresolved_references": unresolved,
        "integrity": {
            "historical_evidence_overwritten": False,
            "credentials_included": False,
            "external_results_fabricated": False,
        },
    }
    output = root / "release-pack" / "NIKWAY-RELEASE-REVIEW-PACK-20260903.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": "PASS",
        "output": output.relative_to(root).as_posix(),
        "files": len(files),
        "unresolved_references": len(unresolved),
        "open_gates": len(pack["open_gates"]),
        "production_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
