"""Abstract interface for secret/credential stores (Vault, AWS Secrets Manager, env vars).

Agent 2 log connectors depend on this interface to retrieve SSH keys and
service account credentials without hardcoding secrets in config files.
"""

from abc import ABC, abstractmethod


class VaultInterface(ABC):
    """Contract for retrieving secrets from any credential backend.

    Implementations must never log or surface the secret value itself.
    All agents reference secrets by key name only.
    """

    @abstractmethod
    def get_secret(self, key: str) -> str:
        """Retrieve a secret by key name.

        Args:
            key: The secret identifier (e.g. 'CDP_SSH_KEY', 'GCP_SA_JSON').

        Returns:
            The secret value as a string.

        Raises:
            VaultSecretNotFoundError: If the key does not exist in the store.
            VaultUnavailableError: If the secret store cannot be reached.
        """
