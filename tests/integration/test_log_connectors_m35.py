"""Integration tests for M3.5 stub connectors.

Verifies that:
- All M3.5 cloud stub connectors raise NotImplementedError (expected — full
  implementations are planned for the M3.5 feature tickets ARI-50/51/52)
- SSHLogConnector (onprem) and GCPLogConnector still import and instantiate
  correctly after the clusters/ restructure (ARI-67 regression guard)
- Oracle and Kafka log access is handled by SSHLogConnector — no separate
  connector class needed since both are SSH-reachable clusters

No real external services are required. Cloud stub tests are purely structural.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from core.models import PlatformTag

# ── Cloud stub connectors ─────────────────────────────────────────────────────


class TestDatabricksStub:
    def test_raises_not_implemented(self):
        from implementations.clusters.cloud.databricks.log_connector import DatabricksLogConnector

        connector = DatabricksLogConnector()
        with pytest.raises(NotImplementedError, match="[Dd]atabricks"):
            connector.query_logs(
                host="dbc-cluster-01",
                platform_tag=PlatformTag.DATABRICKS,
                start_time=datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 4, 16, 1, 0, tzinfo=timezone.utc),
            )


class TestAWSEMRStub:
    def test_raises_not_implemented(self):
        from implementations.clusters.cloud.aws.log_connector import AWSEMRLogConnector

        connector = AWSEMRLogConnector()
        with pytest.raises(NotImplementedError, match="[Aa][Ww][Ss]|[Ee][Mm][Rr]"):
            connector.query_logs(
                host="emr-cluster-01",
                platform_tag=PlatformTag.AWS,
                start_time=datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 4, 16, 1, 0, tzinfo=timezone.utc),
            )


class TestAzureStub:
    def test_raises_not_implemented(self):
        from implementations.clusters.cloud.azure.log_connector import AzureLogConnector

        connector = AzureLogConnector()
        with pytest.raises(NotImplementedError, match="[Aa]zure"):
            connector.query_logs(
                host="aks-cluster-01",
                platform_tag=PlatformTag.AZURE,
                start_time=datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 4, 16, 1, 0, tzinfo=timezone.utc),
            )


# ── SSHLogConnector import + instantiation (ARI-67 regression guard) ──────────


class TestSSHLogConnectorImport:
    def test_imports_from_new_path(self):
        from implementations.clusters.onprem.log_connector import SSHLogConnector

        assert SSHLogConnector is not None

    def test_instantiates_with_required_params(self):
        from implementations.clusters.onprem.log_connector import SSHLogConnector

        connector = SSHLogConnector(
            vault=MagicMock(),
            ssh_key_secret="TEST_KEY",
            ssh_user="hadoop",
            log_dirs=["/var/log/hadoop-hdfs"],
        )
        assert connector is not None

    def test_old_cdp_path_no_longer_exists(self):
        with pytest.raises(ModuleNotFoundError):
            import implementations.cdp.log_connector  # noqa: F401


# ── GCPLogConnector import + instantiation (ARI-67 regression guard) ─────────


class TestGCPLogConnectorImport:
    def test_imports_from_new_path(self):
        from implementations.clusters.cloud.gcp.log_connector import GCPLogConnector

        assert GCPLogConnector is not None

    def test_instantiates(self):
        from implementations.clusters.cloud.gcp.log_connector import GCPLogConnector

        connector = GCPLogConnector(vault=MagicMock())
        assert connector is not None

    def test_old_gcp_path_no_longer_exists(self):
        with pytest.raises(ModuleNotFoundError):
            import implementations.gcp.log_connector  # noqa: F401


# ── Oracle + Kafka: SSHLogConnector handles both ──────────────────────────────


class TestOracleKafkaViaSSH:
    """Oracle RAC and Kafka broker logs are on SSH-reachable nodes.
    SSHLogConnector handles them — no dedicated connector class needed.
    """

    def test_ssh_connector_usable_for_oracle(self):
        from implementations.clusters.onprem.log_connector import SSHLogConnector

        connector = SSHLogConnector(
            vault=MagicMock(),
            ssh_key_secret="ORACLE_SSH_KEY",
            ssh_user="oracle",
            log_dirs=["/u01/app/oracle/diag/rdbms", "/u01/app/oracle/product/log"],
        )
        assert connector is not None

    def test_ssh_connector_usable_for_kafka(self):
        from implementations.clusters.onprem.log_connector import SSHLogConnector

        connector = SSHLogConnector(
            vault=MagicMock(),
            ssh_key_secret="KAFKA_SSH_KEY",
            ssh_user="kafka",
            log_dirs=["/var/log/kafka"],
        )
        assert connector is not None
