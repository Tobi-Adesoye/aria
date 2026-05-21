"""Abstract interface for log stores (BigQuery, Splunk, ELK, local files, etc.).

Agent 2 (Log Finder) depends on this interface.
Concrete implementations live in /implementations/.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from core.models import LogQueryResult, PlatformTag


class LogStoreInterface(ABC):
    """Contract for querying logs from any log storage backend.

    Implementations must apply time windowing and platform filtering.
    They must never block the pipeline when no logs are found —
    return an empty LogQueryResult with confidence=low instead.
    """

    @abstractmethod
    def query_logs(
        self,
        host: str,
        platform_tag: PlatformTag,
        start_time: datetime,
        end_time: datetime,
        keywords: list[str] | None = None,
        log_paths: list[str] | None = None,
        max_results: int = 50,
    ) -> LogQueryResult:
        """Query logs for a host within a time window.

        Selection logic (must be respected by all implementations):
        - Filter by exact host match, or fuzzy match (Levenshtein distance <= 2)
        - Level priority: ERROR first, then WARN, then INFO
        - Truncate at max_results
        - If no results: implementations should NOT raise — return empty result

        Args:
            host: Hostname or resource name extracted from the incident.
            platform_tag: Platform the host belongs to (cdp, gcp, aws, etc.).
            start_time: Start of the query window (typically incident_time - 30min).
            end_time: End of the query window (typically incident_time + 5min).
            keywords: Optional keyword list for targeted filtering (from KB hints).
            log_paths: Optional log file/directory paths to search (from KB hints).
            max_results: Maximum number of log lines to return.

        Returns:
            LogQueryResult with matched log lines and query metadata.
            Returns empty log_lines list if no logs found — never raises.

        Raises:
            LogQueryTimeoutError: If the query exceeds the time budget.
            LogStoreUnavailableError: If the log store cannot be reached.
        """
