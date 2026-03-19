from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets
import os
import warnings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Digital Bank Pro"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # Database - use SQLite for local dev
    DATABASE_URL: str = "sqlite+aiosqlite:///./bank.db"

    # Database Pool Settings (for PostgreSQL)
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # ARQ Worker
    ARQ_REDIS_URL: str = "redis://localhost:6379"

    # Per-User Rate Limiting
    USER_RATE_LIMIT_PER_MINUTE: int = 120
    USER_RATE_LIMIT_PER_HOUR: int = 1000
    USER_RATE_LIMIT_PER_DAY: int = 5000

    # Database Read Replica (for analytics)
    DATABASE_REPLICA_URL: str = ""

    # Secrets Backend
    SECRETS_BACKEND: str = "env"  # Options: env, vault, aws_secrets
    VAULT_URL: str = "http://localhost:8200"
    VAULT_TOKEN: str = ""
    VAULT_PATH: str = "digital-bank"
    AWS_REGION: str = "us-east-1"
    AWS_SECRET_NAME: str = "digital-bank/secrets"

    # JWT
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def use_secrets_manager(self) -> bool:
        """Check if secrets manager should be used."""
        return self.SECRETS_BACKEND != "env" and self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __post_init__(self):
        # Generate a secret key if not set (development only)
        if not self.SECRET_KEY:
            env_key = os.getenv("SECRET_KEY")
            if env_key:
                self.SECRET_KEY = env_key
            else:
                warnings.warn(
                    "SECRET_KEY not set in environment. Using generated key. "
                    "DO NOT use in production!",
                    RuntimeWarning
                )
                self.SECRET_KEY = secrets.token_urlsafe(64)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
