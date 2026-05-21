"""Env-var backed VaultInterface stub for local development and CI.

Reads secrets from environment variables. Not suitable for production —
use HashiCorp Vault or AWS Secrets Manager in real deployments.
"""

import os

from core.exceptions import VaultSecretNotFoundError
from core.interfaces.vault import VaultInterface


class EnvVarVault(VaultInterface):
    """Resolves secrets from environment variables.

    Key names are looked up exactly as provided (case-sensitive).
    Set ARIA_VAULT_PREFIX to namespace all keys (e.g. prefix='ARIA_' means
    get_secret('CDP_KEY') reads env var 'ARIA_CDP_KEY').
    """

    def __init__(self, prefix: str = "") -> None:
        self._prefix = prefix

    def get_secret(self, key: str) -> str:
        env_key = f"{self._prefix}{key}"
        value = os.environ.get(env_key)
        if value is None:
            raise VaultSecretNotFoundError(f"Secret '{env_key}' not found in environment")
        return value
