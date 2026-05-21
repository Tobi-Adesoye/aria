"""Unit tests for vault implementations — all backends mocked, no real credentials."""

import json
from unittest.mock import MagicMock, patch

import pytest

from core.exceptions import VaultSecretNotFoundError, VaultUnavailableError
from implementations.vault.envvar import EnvVarVault

# ── EnvVarVault ──────────────────────────────────────────────────────────────


class TestEnvVarVault:
    def test_returns_value_from_env(self, monkeypatch):
        monkeypatch.setenv("MY_SECRET", "s3cr3t")
        assert EnvVarVault().get_secret("MY_SECRET") == "s3cr3t"

    def test_prefix_is_applied(self, monkeypatch):
        monkeypatch.setenv("ARIA_MY_KEY", "val")
        assert EnvVarVault(prefix="ARIA_").get_secret("MY_KEY") == "val"

    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("MISSING_KEY", raising=False)
        with pytest.raises(VaultSecretNotFoundError, match="MISSING_KEY"):
            EnvVarVault().get_secret("MISSING_KEY")


# ── HashiCorpVaultClient ──────────────────────────────────────────────────────


class TestHashiCorpVaultClient:
    def _make_client(self, mock_hvac_client):
        from implementations.vault.hashicorp import HashiCorpVaultClient

        with patch("implementations.vault.hashicorp.hvac.Client", return_value=mock_hvac_client):
            return HashiCorpVaultClient(url="http://vault:8200", token="test-token")

    def test_returns_value_field(self):
        mock = MagicMock()
        mock.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "my-secret"}}
        }
        client = self._make_client(mock)
        assert client.get_secret("MY_KEY") == "my-secret"

    def test_missing_value_field_raises(self):
        mock = MagicMock()
        mock.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"other_field": "x"}}
        }
        client = self._make_client(mock)
        with pytest.raises(VaultSecretNotFoundError, match="no 'value' field"):
            client.get_secret("MY_KEY")

    def test_invalid_path_raises_not_found(self):
        from hvac.exceptions import InvalidPath

        mock = MagicMock()
        mock.secrets.kv.v2.read_secret_version.side_effect = InvalidPath()
        client = self._make_client(mock)
        with pytest.raises(VaultSecretNotFoundError, match="MY_KEY"):
            client.get_secret("MY_KEY")

    def test_forbidden_raises_unavailable(self):
        from hvac.exceptions import Forbidden

        mock = MagicMock()
        mock.secrets.kv.v2.read_secret_version.side_effect = Forbidden()
        client = self._make_client(mock)
        with pytest.raises(VaultUnavailableError, match="Access denied"):
            client.get_secret("MY_KEY")

    def test_vault_down_raises_unavailable(self):
        from hvac.exceptions import VaultDown

        mock = MagicMock()
        mock.secrets.kv.v2.read_secret_version.side_effect = VaultDown()
        client = self._make_client(mock)
        with pytest.raises(VaultUnavailableError, match="sealed or unreachable"):
            client.get_secret("MY_KEY")

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://vault:8200")
        monkeypatch.setenv("VAULT_TOKEN", "tok")
        from implementations.vault.hashicorp import HashiCorpVaultClient

        with patch("implementations.vault.hashicorp.hvac.Client") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = HashiCorpVaultClient.from_env()
        assert client is not None

    def test_from_env_missing_addr_raises(self, monkeypatch):
        monkeypatch.delenv("VAULT_ADDR", raising=False)
        monkeypatch.delenv("VAULT_TOKEN", raising=False)
        from implementations.vault.hashicorp import HashiCorpVaultClient

        with pytest.raises(VaultUnavailableError, match="VAULT_ADDR"):
            HashiCorpVaultClient.from_env()


# ── AWSSecretsManagerVault ────────────────────────────────────────────────────


class TestAWSSecretsManagerVault:
    def _make_client(self, mock_boto_client):
        from implementations.vault.aws_sm import AWSSecretsManagerVault

        with patch("implementations.vault.aws_sm.boto3.client", return_value=mock_boto_client):
            return AWSSecretsManagerVault(region_name="eu-west-1")

    def test_returns_plain_string(self):
        mock = MagicMock()
        mock.get_secret_value.return_value = {"SecretString": "plain-secret"}
        client = self._make_client(mock)
        assert client.get_secret("MY_KEY") == "plain-secret"

    def test_returns_value_from_json(self):
        mock = MagicMock()
        mock.get_secret_value.return_value = {
            "SecretString": json.dumps({"value": "json-secret", "other": "x"})
        }
        client = self._make_client(mock)
        assert client.get_secret("MY_KEY") == "json-secret"

    def test_returns_full_json_string_when_no_value_key(self):
        payload = json.dumps({"user": "admin", "pass": "123"})
        mock = MagicMock()
        mock.get_secret_value.return_value = {"SecretString": payload}
        client = self._make_client(mock)
        assert client.get_secret("MY_KEY") == payload

    def test_not_found_raises(self):
        from botocore.exceptions import ClientError

        mock = MagicMock()
        mock.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "GetSecretValue",
        )
        client = self._make_client(mock)
        with pytest.raises(VaultSecretNotFoundError, match="MY_KEY"):
            client.get_secret("MY_KEY")

    def test_access_denied_raises_unavailable(self):
        from botocore.exceptions import ClientError

        mock = MagicMock()
        mock.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "GetSecretValue"
        )
        client = self._make_client(mock)
        with pytest.raises(VaultUnavailableError, match="Access denied"):
            client.get_secret("MY_KEY")

    def test_binary_secret_raises(self):
        mock = MagicMock()
        mock.get_secret_value.return_value = {"SecretBinary": b"binary", "SecretString": None}
        client = self._make_client(mock)
        with pytest.raises(VaultSecretNotFoundError, match="binary"):
            client.get_secret("MY_KEY")

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
        from implementations.vault.aws_sm import AWSSecretsManagerVault

        with patch("implementations.vault.aws_sm.boto3.client") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = AWSSecretsManagerVault.from_env()
        assert client is not None

    def test_from_env_missing_region_raises(self, monkeypatch):
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_REGION", raising=False)
        from implementations.vault.aws_sm import AWSSecretsManagerVault

        with pytest.raises(VaultUnavailableError, match="AWS_DEFAULT_REGION"):
            AWSSecretsManagerVault.from_env()


# ── AzureKeyVaultClient ───────────────────────────────────────────────────────


class TestAzureKeyVaultClient:
    def _make_client(self, mock_secret_client):
        from implementations.vault.azure_kv import AzureKeyVaultClient

        with patch("implementations.vault.azure_kv.DefaultAzureCredential"), patch(
            "implementations.vault.azure_kv.SecretClient", return_value=mock_secret_client
        ):
            return AzureKeyVaultClient(vault_url="https://my-vault.vault.azure.net/")

    def test_returns_secret_value(self):
        mock = MagicMock()
        mock.get_secret.return_value = MagicMock(value="azure-secret")
        client = self._make_client(mock)
        assert client.get_secret("MY_KEY") == "azure-secret"

    def test_underscore_converted_to_hyphen(self):
        mock = MagicMock()
        mock.get_secret.return_value = MagicMock(value="val")
        client = self._make_client(mock)
        client.get_secret("CDP_SSH_KEY")
        mock.get_secret.assert_called_once_with("CDP-SSH-KEY")

    def test_not_found_raises(self):
        from azure.core.exceptions import ResourceNotFoundError

        mock = MagicMock()
        mock.get_secret.side_effect = ResourceNotFoundError()
        client = self._make_client(mock)
        with pytest.raises(VaultSecretNotFoundError, match="MY_KEY"):
            client.get_secret("MY_KEY")

    def test_forbidden_raises_unavailable(self):
        from azure.core.exceptions import HttpResponseError

        mock = MagicMock()
        err = HttpResponseError()
        err.status_code = 403
        mock.get_secret.side_effect = err
        client = self._make_client(mock)
        with pytest.raises(VaultUnavailableError, match="Access denied"):
            client.get_secret("MY_KEY")

    def test_service_request_error_raises_unavailable(self):
        from azure.core.exceptions import ServiceRequestError

        mock = MagicMock()
        mock.get_secret.side_effect = ServiceRequestError(message="timeout")
        client = self._make_client(mock)
        with pytest.raises(VaultUnavailableError, match="unreachable"):
            client.get_secret("MY_KEY")

    def test_none_value_raises_not_found(self):
        mock = MagicMock()
        mock.get_secret.return_value = MagicMock(value=None)
        client = self._make_client(mock)
        with pytest.raises(VaultSecretNotFoundError, match="no value"):
            client.get_secret("MY_KEY")

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("AZURE_VAULT_URL", "https://my-vault.vault.azure.net/")
        from implementations.vault.azure_kv import AzureKeyVaultClient

        with patch("implementations.vault.azure_kv.DefaultAzureCredential"), patch(
            "implementations.vault.azure_kv.SecretClient"
        ):
            client = AzureKeyVaultClient.from_env()
        assert client is not None

    def test_from_env_missing_url_raises(self, monkeypatch):
        monkeypatch.delenv("AZURE_VAULT_URL", raising=False)
        from implementations.vault.azure_kv import AzureKeyVaultClient

        with pytest.raises(VaultUnavailableError, match="AZURE_VAULT_URL"):
            AzureKeyVaultClient.from_env()
