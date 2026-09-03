"""Validate the NIKWAY security and CI contracts without contacting externals."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    security = yaml.safe_load(
        (root / "publish-ready-sample" / "V1_SECURITY_CONFIG.yaml").read_text(
            encoding="utf-8"
        )
    )
    compose = yaml.safe_load(
        (root / "publish-ready-sample" / "docker-compose.full-v1.yml").read_text(
            encoding="utf-8"
        )
    )
    workflow = yaml.safe_load(
        (
            root
            / "publish-ready-sample"
            / ".github"
            / "workflows"
            / "security-scan.yml"
        ).read_text(encoding="utf-8")
    )

    checks = {
        "oidc_protocol": security["authentication"]["protocol"] == "OIDC",
        "jwks_required": bool(security["authentication"].get("jwks_env")),
        "password_storage_forbidden": security["authentication"]["password_storage"]
        == "forbidden",
        "deny_by_default": security["authorization"]["default"] == "deny",
        "cors_wildcard_forbidden": security["cors"]["wildcard_allowed"] is False,
        "secrets_externalized": security["secrets"]["repository_storage"] == "forbidden",
        "runtime_superuser_forbidden": security["database"]["superuser"] == "forbidden",
        "compose_runtime_role_distinct": "nikway_runtime" in compose["services"]["api"][
            "environment"
        ]["DATABASE_URL"],
        "compose_oidc_jwks_required": "OIDC_JWKS_URL" in str(
            compose["services"]["api"]["environment"]
        ),
    }
    scan_steps = [
        step
        for step in workflow["jobs"]["dependency-scan"]["steps"]
        if "with" in step and step["with"].get("scan-type") == "fs"
    ]
    checks["ci_scan_configured"] = len(scan_steps) == 1
    checks["ci_scan_fails_on_findings"] = scan_steps[0]["with"].get("exit-code") == "1"
    checks["ci_report_upload"] = any(
        step.get("name") == "Upload Trivy report"
        and step.get("with", {}).get("path") == "trivy-fs-report.json"
        for step in workflow["jobs"]["dependency-scan"]["steps"]
    ) or any(
        step.get("name") == "Upload Trivy report"
        and "trivy-fs-report.json" in step.get("with", {}).get("path", "")
        for step in workflow["jobs"]["dependency-scan"]["steps"]
    )

    failed = [name for name, passed in checks.items() if not passed]
    result = {"result": "PASS" if not failed else "FAIL", "checks": checks}
    if failed:
        result["failed"] = failed
    print(json.dumps(result, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
