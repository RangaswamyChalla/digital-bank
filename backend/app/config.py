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