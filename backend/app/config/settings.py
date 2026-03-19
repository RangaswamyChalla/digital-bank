"""
Environment configuration management for the banking application.
Handles loading and validation of environment variables for all services.
"""

import os
from typing import Optional
from pydantic import BaseSettings, validator


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    url: str = "sqlite:///./bank.db"
    pool_size: int = 20
    max_overflow: int = 40
    echo_sql: bool = False

    class Config:
        env_prefix = "DB_"


class AuthSettings(BaseSettings):
    """Authentication configuration"""

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_audience: str = "banking-app"

    @validator("secret_key")
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-in-production":
            print(
                "⚠️  WARNING: Using default secret key! Change JWT_SECRET_KEY in production"
            )
        return v

    class Config:
        env_prefix = "JWT_"


class RedisSettings(BaseSettings):
    """Redis configuration (optional for caching)"""

    enabled: bool = False
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    @property
    def url(self):
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class AiServiceSettings(BaseSettings):
    """AI/Fraud detection service configuration"""

    enabled: bool = True
    timeout_seconds: int = 10
    max_retries: int = 3
    retry_delay_seconds: int = 1

    class Config:
        env_prefix = "AI_"


class LoggingSettings(BaseSettings):
    """Logging configuration"""

    level: str = "INFO"
    format: str = "json"  # json or plain
    file_path: Optional[str] = None  # If set, logs will be written to file

    class Config:
        env_prefix = "LOG_"


class SecuritySettings(BaseSettings):
    """Security configuration"""

    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1"
    max_request_size_mb: int = 10

    @property
    def cors_origins_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_hosts_list(self):
        return [host.strip() for host in self.allowed_hosts.split(",")]

    class Config:
        env_prefix = "SECURITY_"


class WebSocketSettings(BaseSettings):
    """WebSocket configuration"""

    max_connections_per_user: int = 5
    heartbeat_interval_seconds: int = 30
    connection_timeout_seconds: int = 300

    class Config:
        env_prefix = "WS_"


class ApplicationSettings(BaseSettings):
    """Main application configuration"""

    app_name: str = "Digital Banking Platform"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    auth: AuthSettings = AuthSettings()
    redis: RedisSettings = RedisSettings()
    ai: AiServiceSettings = AiServiceSettings()
    logging: LoggingSettings = LoggingSettings()
    security: SecuritySettings = SecuritySettings()
    websocket: WebSocketSettings = WebSocketSettings()

    @validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Invalid environment. Must be development, staging, or production")
        return v

    @validator("debug", pre=True, always=True)
    def set_debug(cls, v, values):
        # Debug should be True only in development
        env = values.get("environment", "development")
        return env == "development"

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


def get_settings() -> ApplicationSettings:
    """Get application settings (singleton pattern)"""
    return ApplicationSettings()
