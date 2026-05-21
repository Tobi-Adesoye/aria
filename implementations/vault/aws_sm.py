"""AWS Secrets Manager implementation of VaultInterface.

Retrieves secrets from AWS Secrets Manager. Suitable for deployments running
on AWS (EC2, ECS, Lambda) where IAM roles provide implicit authentication.
"""

import json
import os

import boto3
from botocore.exceptions import ClientError, EndpointResolutionError, NoCredentialsError

from core.exceptions import VaultSecretNotFoundError, VaultUnavailableError
from core.interfaces.vault import VaultInterface


class AWSSecretsManagerVault(VaultInterface):
    """Retrieves secrets from AWS Secrets Manager.

    Secrets may be stored as plain strings or as JSON objects. When the stored
    value is valid JSON, ``get_secret`` looks for a ``value`` key first; if not
    present the entire JSON string is returned so callers can parse it themselves.

    Authentication uses the standard boto3 credential chain: IAM role, env vars
    (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY), or ~/.aws/credentials.

    Instantiate via ``from_env()`` in production or inject directly in tests.
    """

    def __init__(
        self,
        region_name: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        try:
            self._client = boto3.client(
                "secretsmanager",
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        except Exception as exc:
            raise VaultUnavailableError(
                f"Failed to initialise AWS Secrets Manager client: {exc}"
            ) from exc

    @classmethod
    def from_env(cls) -> "AWSSecretsManagerVault":
        """Construct from environment variables.

        Required: AWS_DEFAULT_REGION (or AWS_REGION)
        Optional: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (falls back to IAM role)
        """
        region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION")
        if not region:
            raise VaultUnavailableError(
                "AWS_DEFAULT_REGION or AWS_REGION environment variable is required"
            )
        return cls(
            region_name=region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )

    def get_secret(self, key: str) -> str:
        try:
            response = self._client.get_secret_value(SecretId=key)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("ResourceNotFoundException", "SecretNotFoundException"):
                raise VaultSecretNotFoundError(
                    f"Secret '{key}' not found in AWS Secrets Manager"
                ) from exc
            if code in ("AccessDeniedException", "InvalidRequestException"):
                raise VaultUnavailableError(f"Access denied reading secret '{key}': {exc}") from exc
            raise VaultUnavailableError(
                f"AWS Secrets Manager error reading '{key}': {exc}"
            ) from exc
        except NoCredentialsError as exc:
            raise VaultUnavailableError(
                "No AWS credentials found — configure IAM role or env vars"
            ) from exc
        except EndpointResolutionError as exc:
            raise VaultUnavailableError(f"AWS Secrets Manager endpoint unreachable: {exc}") from exc

        raw = response.get("SecretString")
        if raw is None:
            raise VaultSecretNotFoundError(
                f"Secret '{key}' is binary — only string secrets are supported"
            )

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "value" in parsed:
                return parsed["value"]
        except json.JSONDecodeError:
            pass

        return raw
