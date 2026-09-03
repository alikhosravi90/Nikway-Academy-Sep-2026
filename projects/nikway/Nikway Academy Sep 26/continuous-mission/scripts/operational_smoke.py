"""Read-only local operational smoke checks for NIKWAY.

The command intentionally reports local runtime facts only. It does not
promote a release, mutate services, or infer staging readiness.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def http_check(url: str, *, parse_json: bool = False) -> dict:
    try:
        with urlopen(url, timeout=5) as response:
            body = response.read()
            result = {"status": "PASS_LOCAL", "http_status": response.status}
            if parse_json:
                payload = json.loads(body.decode("utf-8"))
                result["payload"] = payload
            return result
    except HTTPError as error:
        return {"status": "NOT_APPLICABLE" if error.code == 404 else "FAIL_LOCAL", "http_status": error.code}
    except (URLError, TimeoutError, OSError) as error:
        return {"status": "UNREACHABLE_LOCAL", "error": type(error).__name__}


def docker_services() -> dict:
    try:
        completed = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Status}}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        return {"status": "UNAVAILABLE_LOCAL", "error": type(error).__name__}
    services = {}
    for line in completed.stdout.splitlines():
        if "|" in line:
            name, status = line.split("|", 1)
            if any(token in name for token in ("nikway", "keycloak", "minio")):
                services[name] = status
    return {"status": "PASS_LOCAL", "services": services}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8001")
    parser.add_argument("--oidc", default="http://127.0.0.1:8081/realms/master")
    parser.add_argument("--minio", default="http://127.0.0.1:9000")
    args = parser.parse_args()

    discovery = http_check(
        f"{args.oidc}/.well-known/openid-configuration", parse_json=True
    )
    jwks = {"status": "NOT_RUN"}
    if discovery.get("status") == "PASS_LOCAL":
        jwks_uri = discovery["payload"].get("jwks_uri")
        if jwks_uri:
            jwks = http_check(jwks_uri, parse_json=True)
            if jwks.get("status") == "PASS_LOCAL":
                keys = jwks["payload"].get("keys", [])
                jwks["key_count"] = len(keys)
                jwks.pop("payload", None)

    checks = {
        "api_health": http_check(f"{args.api}/health", parse_json=True),
        "api_dependencies": http_check(f"{args.api}/health/dependencies", parse_json=True),
        "api_readiness": http_check(f"{args.api}/health/ready", parse_json=True),
        "oidc_discovery": discovery,
        "oidc_jwks": jwks,
        "minio_health": http_check(f"{args.minio}/minio/health/live"),
        "docker_services": docker_services(),
    }
    # Do not print discovery claims or response bodies; only safe operational facts.
    checks["oidc_discovery"].pop("payload", None)
    for key in ("api_health", "api_dependencies", "api_readiness"):
        checks[key].pop("payload", None)
    print(json.dumps(checks, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
