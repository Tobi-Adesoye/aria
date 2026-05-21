"""HashiCorp Vault implementation of VaultInterface.

Reads secrets from a KV v2 secrets engine. Suitable for production deployments
where secrets are managed centrally via HashiCorp Vault.
"""

import os

import hvac
from hvac.exceptions import Forbidden, InvalidPath, VaultDown, VaultError

from core.exceptions import VaultSecretNotFoundError, VaultUnavailableError
from core.interfaces.vault import VaultInterface


class HashiCorpVaultClient(VaultInterface):
    """Retrieves secrets from HashiCorp Vault KV v2 secrets engine.

    Secrets are expected to be stored as key/value pairs under a `value` field:
        vault kv put secret/MY_KEY value=my-secret-value

    Instantiate via ``from_env()`` in production or inject directly in tests.
    """

    def __init__(
        self,
        url: str,
        token: str,
        mount_path: str = "secret",
        namespace: str | None = None,
    ) -> None:
        self._mount_path = mount_path
        try:
            self._client = hvac.Client(url=url, token=token, namespace=namespace)
        except Exception as exc:
            raise VaultUnavailableError(
                f"Failed to initialise HashiCorp Vault client: {exc}"
            ) from exc

    @classmethod
    def from_env(cls) -> "HashiCorpVaultClient":
        """Construct from environment variables.

        Required: VAULT_ADDR, VAULT_TOKEN
        Optional: VAULT_MOUNT_PATH (default: secret), VAULT_NAMESPACE
        """
        url = os.environ.get("VAULT_ADDR")
        token = os.environ.get("VAULT_TOKEN")
        if not url or not token:
            raise VaultUnavailableError(
                "VAULT_ADDR and VAULT_TOKEN environment variables are required"
            )
        return cls(
            url=url,
            token=token,
            mount_path=os.environ.get("VAULT_MOUNT_PATH", "secret"),
            namespace=os.environ.get("VAULT_NAMESPACE"),
        )

    def get_secret(self, key: str) -> str:
        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=key,
                mount_point=self._mount_path,
                raise_on_deleted_version=True,
            )
            data = response["data"]["data"]
            if "value" not in data:
                raise VaultSecretNotFoundError(
                    f"Secret '{key}' exists but has no 'value' field — "
                    "store secrets with: vault kv put <mount>/<key> value=<secret>"
                )
            return data["value"]
        except (InvalidPath, KeyError):
            raise VaultSecretNotFoundError(f"Secret '{key}' not found in HashiCorp Vault")
        except Forbidden as exc:
            raise VaultUnavailableError(f"Access denied reading secret '{key}': {exc}") from exc
        except VaultDown as exc:
            raise VaultUnavailableError(f"HashiCorp Vault is sealed or unreachable: {exc}") from exc
        except VaultError as exc:
            raise VaultUnavailableError(f"HashiCorp Vault error reading '{key}': {exc}") from exc
