import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class Settings:
    # API Configurations
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bdis_prod.db")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Infrastructure
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "bdis-documents-archive")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Financial Policies
    BASE_CURRENCY: str = "USD"
    # Fallback rates if no live FX service is connected
    FIXED_FX_RATES: dict = None

    # Auth (Phase 6)
    # - dev_headers: allow X-BDIS-* headers (dev only)
    # - none: reject identity headers (default until OIDC is implemented)
    BDIS_AUTH_MODE: str = os.getenv("BDIS_AUTH_MODE", "none")

    # OIDC (Phase 6 - Mode B)
    OIDC_JWKS_URL: str | None = os.getenv("OIDC_JWKS_URL")
    OIDC_ISSUER: str | None = os.getenv("OIDC_ISSUER")
    OIDC_AUDIENCE: str | None = os.getenv("OIDC_AUDIENCE")
    OIDC_JWT_ALG: str = os.getenv("OIDC_JWT_ALG", "RS256")  # RS256 in production; HS256 for offline tests
    OIDC_JWT_SECRET: str | None = os.getenv("OIDC_JWT_SECRET")  # used for HS256

    def __post_init__(self):
        self.FIXED_FX_RATES = {
            "USD": 1.0,
            "EUR": 1.08,
            "GBP": 1.26,
            "CAD": 0.74,
            "JPY": 0.0066
        }

    def validate(self):
        """Proactively checks for critical missing configuration."""
        if not self.OPENAI_API_KEY:
            print("⚠️ WARNING: OPENAI_API_KEY is missing. Extraction will run in Mock Mode.")

# Singleton instance
settings = Settings()
