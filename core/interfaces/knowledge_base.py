"""Abstract interface for knowledge base / runbook stores.

Dual-use interface:
  - Agent 1 (ARI-46): get_service_hints() drives cluster→service resolution
    when cmdb_ci is a cluster or absent.
  - Agent 2 (ARI-14): get_log_hints() directs log connector dispatch by
    returning known log paths and aggregator endpoints for a service.

Concrete implementations:
  - FileKeywordKB (ARI-59): keyword matching against local runbook YAML/JSON files.
  - RAG-backed implementations: community-provided (Chroma, pgvector, etc.).
"""

from abc import ABC, abstractmethod

from core.models import LogAccessHint, PlatformTag


class KnowledgeBaseInterface(ABC):
    """Contract for querying a knowledge base about services and their logs."""

    @abstractmethod
    def get_service_hints(self, cluster: str, description: str) -> list[str]:
        """Return candidate service/node names for cluster→service resolution.

        Called by Agent 1 when the affected CI is a cluster or unknown.
        The LLM uses these hints to narrow down the specific affected service.

        Args:
            cluster: Cluster name or CI identifier (e.g. 'cdp-prod-cluster-01').
            description: Raw incident description text.

        Returns:
            Ordered list of candidate service names (most likely first).
            Returns an empty list if no hints are available — never raises.

        Raises:
            KnowledgeBaseError: Only if the KB backend is unreachable (not for
                empty results — those are returned as an empty list).
        """

    @abstractmethod
    def get_log_hints(self, service: str, platform_tag: PlatformTag) -> LogAccessHint:
        """Return log access guidance for a service on a given platform.

        Called by Agent 2 as the KB fallback path when the aggregator fast
        path returns no results or is unavailable.

        Args:
            service: Resolved service or node name (e.g. 'hive-metastore').
            platform_tag: Platform the service runs on.

        Returns:
            LogAccessHint with log paths, keywords, and optional aggregator endpoint.
            Returns a hint with empty lists if no entry exists — never raises.

        Raises:
            KnowledgeBaseError: Only if the KB backend is unreachable.
        """
