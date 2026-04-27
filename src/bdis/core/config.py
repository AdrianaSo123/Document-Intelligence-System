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
