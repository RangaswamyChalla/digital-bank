"""
Secrets Manager Integration for Digital Bank.
Supports HashiCorp Vault, AWS Secrets Manager, or environment variable fallback.
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecretBackend(str, Enum):
    """Supported secret backend types."""
    VAULT = "vault"
    AWS_SECRETS = "aws_secrets"
    ENV = "env"  # Fallback to environment variables


@dataclass
class SecretConfig:
    """Configuration for secrets backend."""
    backend: SecretBackend = SecretBackend.ENV
    # HashiCorp Vault config
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    vault_path: str = "digital-bank"
    # AWS Secrets Manager config
    aws_region: Optional[str] = None
    aws_secret_name: Optional[str] = None


class SecretsManager:
    """
    Unified secrets manager with support for multiple backends.

    Priority:
    1. HashiCorp Vault (most secure, production recommended)
    2. AWS Secrets Manager (cloud-native option)
    3. Environment variables (development/fallback)
    """

    def __init__(self, config: Optional[SecretConfig] = None):
        self.config = config or self._load_config()
        self._backend = None
        self._cache: Dict[str, Any] = {}
        self._initialize_backend()

    def _load_config(self) -> SecretConfig:
        """Load secrets configuration from environment variables."""
        backend_str = os.getenv("SECRETS_BACKEND", "env").lower()

        if backend_str == "vault":
            return SecretConfig(
                backend=SecretBackend.VAULT,
                vault_url=os.getenv("VAULT_URL", "http://localhost:8200"),
                vault_token=os.getenv("VAULT_TOKEN"),
                vault_path=os.getenv("VAULT_PATH", "digital-bank"),
            )
        elif backend_str == "aws_secrets":
            return SecretConfig(
                backend=SecretBackend.AWS_SECRETS,
                aws_region=os.getenv("AWS_REGION", "us-east-1"),
                aws_secret_name=os.getenv("AWS_SECRET_NAME", "digital-bank/secrets"),
            )
        else:
            return SecretConfig(backend=SecretBackend.ENV)

    def _initialize_backend(self):
        """Initialize the secrets backend."""
        if self.config.backend == SecretBackend.VAULT:
            self._backend = VaultBackend(self.config)
        elif self.config.backend == SecretBackend.AWS_SECRETS:
            self._backend = AWSSecretsBackend(self.config)
        else:
            self._backend = EnvBackend(self.config)

    async def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value by key.

        Args:
            key: Secret key name
            default: Default value if not found

        Returns:
            Secret value or default
        """
        if key in self._cache:
            return self._cache[key]

        value = await self._backend.get_secret(key)

        if value is None and default is not None:
            value = default

        if value is not None:
            self._cache[key] = value

        return value

    async def get_secrets(self, *keys: str) -> Dict[str, Optional[str]]:
        """
        Get multiple secrets at once.

        Args:
            keys: Secret key names

        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        for key in keys:
            result[key] = await self.get_secret(key)
        return result

    async def set_secret(self, key: str, value: str) -> bool:
        """
        Set a secret value (write mode).

        Note: Only supported for Vault backend.

        Args:
            key: Secret key
            value: Secret value

        Returns:
            True if successful
        """
        success = await self._backend.set_secret(key, value)
        if success:
            self._cache[key] = value
        return success

    def clear_cache(self):
        """Clear the secrets cache."""
        self._cache.clear()
        logger.info("Secrets cache cleared")


class EnvBackend:
    """Environment variable secrets backend (development/fallback)."""

    def __init__(self, config: SecretConfig):
        self.config = config

    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment variable."""
        # Map logical keys to environment variable names
        env_map = {
            "SECRET_KEY": "SECRET_KEY",
            "DATABASE_URL": "DATABASE_URL",
            "REDIS_URL": "REDIS_URL",
            "SENTRY_DSN": "SENTRY_DSN",
            "OTLP_ENDPOINT": "OTLP_ENDPOINT",
        }
        env_key = env_map.get(key, key)
        return os.getenv(env_key)

    async def set_secret(self, key: str, value: str) -> bool:
        """Environment backend doesn't support writes."""
        logger.warning(f"EnvBackend.set_secret called - not supported")
        return False


class VaultBackend:
    """HashiCorp Vault secrets backend."""

    def __init__(self, config: SecretConfig):
        self.config = config
        self._client = None

    async def _get_client(self):
        """Get or create Vault client."""
        if self._client is None:
            try:
                import hvac
                self._client = hvac.Client(url=self.config.vault_url)
                if self.config.vault_token:
                    self._client.token = self.config.vault_token
                logger.info(f"Connected to Vault at {self.config.vault_url}")
            except ImportError:
                logger.error("hvac not installed. Install with: pip install hvac")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Vault: {e}")
                raise
        return self._client

    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Vault."""
        try:
            client = await self._get_client()
            secret_path = f"{self.config.vault_path}/{key}"
            response = client.secrets.kv.v2.read_secret_version(path=secret_path)
            return response["data"]["data"][key]
        except Exception as e:
            logger.error(f"Failed to get secret '{key}' from Vault: {e}")
            return None

    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in Vault."""
        try:
            client = await self._get_client()
            secret_path = f"{self.config.vault_path}/{key}"
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={key: value}
            )
            logger.info(f"Secret '{key}' stored in Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{key}' in Vault: {e}")
            return False


class AWSSecretsBackend:
    """AWS Secrets Manager secrets backend."""

    def __init__(self, config: SecretConfig):
        self.config = config
        self._client = None

    async def _get_client(self):
        """Get or create AWS Secrets Manager client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "secretsmanager",
                    region_name=self.config.aws_region
                )
                logger.info(f"Connected to AWS Secrets Manager in {self.config.aws_region}")
            except ImportError:
                logger.error("boto3 not installed. Install with: pip install boto3")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to AWS Secrets Manager: {e}")
                raise
        return self._client

    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            client = await self._get_client()
            response = client.get_secret_value(SecretId=self.config.aws_secret_name)
            import json
            secrets = json.loads(response["SecretString"])
            return secrets.get(key)
        except Exception as e:
            logger.error(f"Failed to get secret '{key}' from AWS Secrets Manager: {e}")
            return None

    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager."""
        try:
            client = await self._get_client()
            import json
            # Get existing secrets
            try:
                response = client.get_secret_value(SecretId=self.config.aws_secret_name)
                secrets = json.loads(response["SecretString"])
            except client.exceptions.ResourceNotFoundException:
                secrets = {}

            secrets[key] = value

            client.put_secret_value(
                SecretId=self.config.aws_secret_name,
                SecretString=json.dumps(secrets)
            )
            logger.info(f"Secret '{key}' stored in AWS Secrets Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{key}' in AWS Secrets Manager: {e}")
            return False


# Singleton instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the singleton secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


async def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret."""
    manager = get_secrets_manager()
    return await manager.get_secret(key, default)


async def get_secrets(*keys: str) -> Dict[str, Optional[str]]:
    """Convenience function to get multiple secrets."""
    manager = get_secrets_manager()
    return await manager.get_secrets(*keys)
