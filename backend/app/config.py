"""
RazorShield AI — Application Configuration & Settings
Typed configuration model backed by environment variables with strict secret validation.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()


@dataclass
class Settings:
    app_name: str = "RazorShield AI Risk Manager"
    app_version: str = "1.0.0-remediated"
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "local"))

    # Storage Configuration
    postgres_dsn: str = field(default_factory=lambda: os.getenv("POSTGRES_DSN", ""))
    redis_dsn: str = field(default_factory=lambda: os.getenv("REDIS_DSN", ""))
    sqlite_db_path: str = field(
        default_factory=lambda: os.getenv("SQLITE_DB_PATH", "razorshield_local.db")
    )

    # Idempotency Settings
    idempotency_ttl_seconds: int = 86400  # 24 hours

    # Latency Targets (in milliseconds)
    benchmark_latency_target_ms: float = 25.0
    sla_latency_cap_ms: float = 50.0

    # LLM Abstraction Settings
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", ""))
    llm_model_name: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL_NAME", "gemini-3.6-flash")
    )
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    # Secret Key for Audit Signatures (Must be passed via ENV in non-local modes)
    audit_hmac_secret: str = field(
        default_factory=lambda: os.getenv(
            "AUDIT_HMAC_SECRET", "local-dev-secret-placeholder-2026"
        )
    )

    # Environment-Backed RBAC Principal Auth Tokens (None committed in code)
    admin_auth_token: str = field(
        default_factory=lambda: os.getenv("RAZORSHIELD_ADMIN_TOKEN", "")
    )
    analyst_auth_token: str = field(
        default_factory=lambda: os.getenv("RAZORSHIELD_ANALYST_TOKEN", "")
    )
    operator_auth_token: str = field(
        default_factory=lambda: os.getenv("RAZORSHIELD_OPERATOR_TOKEN", "")
    )
    auditor_auth_token: str = field(
        default_factory=lambda: os.getenv("RAZORSHIELD_AUDITOR_TOKEN", "")
    )

    def __post_init__(self):
        if self.environment in ("production", "staging"):
            if not os.getenv("AUDIT_HMAC_SECRET") or self.audit_hmac_secret.startswith(
                "local-dev"
            ):
                raise ValueError(
                    "FATAL CONFIGURATION ERROR: AUDIT_HMAC_SECRET must be explicitly set via environment variable in non-local environments."
                )


settings = Settings()
