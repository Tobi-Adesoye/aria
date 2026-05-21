"""Azure Key Vault implementation of VaultInterface.

Retrieves secrets from Azure Key Vault. Suitable for deployments running on Azure
(AKS, App Service, Azure Functions) where managed identity provides implicit auth.
"""

import os

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from core.exceptions import VaultSecretNotFoundError, VaultUnavailableError
from core.interfaces.vault import VaultInterface


class AzureKeyVaultClient(VaultInterface):
    """Retrieves secrets from Azure Key Vault.

    Authentication uses ``DefaultAzureCredential``, which tries in order:
    environment variables, workload identity, managed identity, Azure CLI, and
    Visual Studio Code credentials. No explicit credential injection needed when
    running on Azure with a managed identity assigned.

    Secret names in Azure Key Vault must be alphanumeric with hyphens only.
    Underscores in ``key`` are automatically converted to hyphens to match the
    Azure naming convention (e.g. ``CDP_SSH_KEY`` → ``CDP-SSH-KEY``).

    Instantiate via ``from_env()`` in production or inject directly in tests.
    """

    def __init__(self, vault_url: str) -> None:
        try:
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=vault_url, credential=credential)
        except Exception as exc:
            raise VaultUnavailableError(
                f"Failed to initialise Azure Key Vault client: {exc}"
            ) from exc

    @classmethod
    def from_env(cls) -> "AzureKeyVaultClient":
        """Construct from environment variables.

        Required: AZURE_VAULT_URL (e.g. https://my-vault.vault.azure.net/)
        """
        url = os.environ.get("AZURE_VAULT_URL")
        if not url:
            raise VaultUnavailableError("AZURE_VAULT_URL environment variable is required")
        return cls(vault_url=url)

    def get_secret(self, key: str) -> str:
        azure_name = key.replace("_", "-")
        try:
            secret = self._client.get_secret(azure_name)
            if secret.value is None:
                raise VaultSecretNotFoundError(f"Secret '{key}' exists but has no value")
            return secret.value
        except ResourceNotFoundError:
            raise VaultSecretNotFoundError(f"Secret '{key}' not found in Azure Key Vault")
        except HttpResponseError as exc:
            if exc.status_code == 403:
                raise VaultUnavailableError(f"Access denied reading secret '{key}': {exc}") from exc
            raise VaultUnavailableError(f"Azure Key Vault error reading '{key}': {exc}") from exc
        except ServiceRequestError as exc:
            raise VaultUnavailableError(f"Azure Key Vault unreachable: {exc}") from exc
