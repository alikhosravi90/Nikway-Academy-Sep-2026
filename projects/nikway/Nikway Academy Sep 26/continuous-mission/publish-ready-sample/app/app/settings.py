import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    database_url: str
    cors_allowed_origins: tuple[str, ...]
    oidc_issuer_url: str
    oidc_audience: str
    oidc_jwks_url: str
    require_auth: bool
    s3_endpoint_url: str
    s3_bucket: str

    @property
    def database_required(self) -> bool:
        return self.environment in {"staging", "production"}


def load_settings() -> RuntimeSettings:
    origins = tuple(
        item.strip()
        for item in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    )
    return RuntimeSettings(
        environment=os.getenv("NIKWAY_ENVIRONMENT", "development"),
        database_url=os.getenv("DATABASE_URL", ""),
        cors_allowed_origins=origins,
        oidc_issuer_url=os.getenv("OIDC_ISSUER_URL", ""),
        oidc_audience=os.getenv("OIDC_AUDIENCE", ""),
        oidc_jwks_url=os.getenv("OIDC_JWKS_URL", ""),
        require_auth=os.getenv("NIKWAY_REQUIRE_AUTH", "false").lower() == "true",
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL", ""),
        s3_bucket=os.getenv("S3_BUCKET", "nikway-evidence"),
    )
