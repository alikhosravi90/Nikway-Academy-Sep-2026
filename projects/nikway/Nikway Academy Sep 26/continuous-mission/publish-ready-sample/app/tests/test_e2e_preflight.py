import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_e2e_procedure_and_environment_contract_are_present():
    contract = ROOT.parent / "external-environment-contract.yaml"
    procedures = ROOT.parent / "verification-procedures.md"
    assert contract.exists()
    assert procedures.exists()
    text = procedures.read_text(encoding="utf-8")
    for case in (
        "authentication",
        "authorization",
        "idempotency",
        "rollback",
        "cleanup",
    ):
        assert case in text


@pytest.mark.integration
def test_real_e2e_preflight_requires_all_external_dependencies():
    required = (
        "DATABASE_URL",
        "OIDC_ISSUER_URL",
        "OIDC_AUDIENCE",
        "OIDC_JWKS_URL",
        "S3_ENDPOINT_URL",
        "S3_BUCKET",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip("real staging E2E is waiting for: " + ", ".join(missing))
