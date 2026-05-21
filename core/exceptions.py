"""Custom exceptions for ARIA domain errors.

Using specific exception types lets callers handle errors precisely
rather than catching broad Exception classes.
"""


class ARIABaseError(Exception):
    """Base class for all ARIA exceptions."""


# ── Connector (ServiceNow) ──────────────────────────────────────────────────


class IncidentNotFoundError(ARIABaseError):
    """Raised when a ServiceNow incident number does not exist (404)."""


class ConnectorAuthError(ARIABaseError):
    """Raised when ServiceNow rejects credentials (401/403)."""


class ConnectorUnavailableError(ARIABaseError):
    """Raised when the ITSM connector cannot be reached (network, timeout)."""


# ── Log store ───────────────────────────────────────────────────────────────


class LogQueryTimeoutError(ARIABaseError):
    """Raised when a log query exceeds the allowed time budget."""


class LogStoreUnavailableError(ARIABaseError):
    """Raised when the log store cannot be reached."""


# ── Queue ───────────────────────────────────────────────────────────────────


class QueuePublishError(ARIABaseError):
    """Raised when a message cannot be published to the queue."""


class QueueSubscribeError(ARIABaseError):
    """Raised when a message cannot be pulled from the queue."""


# ── State store ─────────────────────────────────────────────────────────────


class StateStoreError(ARIABaseError):
    """Raised when a read or write to the state store fails."""


# ── LLM client ──────────────────────────────────────────────────────────────


class LLMAuthError(ARIABaseError):
    """Raised when the LLM provider rejects the API key."""


class LLMUnavailableError(ARIABaseError):
    """Raised when the LLM provider cannot be reached."""


class LLMResponseError(ARIABaseError):
    """Raised when the LLM returns an empty or unparseable response."""


# ── Classification ──────────────────────────────────────────────────────────


class ClassificationError(ARIABaseError):
    """Raised when the LLM classifier returns an unparseable response."""


# ── Vault ───────────────────────────────────────────────────────────────────


class VaultSecretNotFoundError(ARIABaseError):
    """Raised when a requested secret key does not exist in the store."""


class VaultUnavailableError(ARIABaseError):
    """Raised when the secret store cannot be reached."""


# ── Knowledge base ───────────────────────────────────────────────────────────


class KnowledgeBaseError(ARIABaseError):
    """Raised when the knowledge base cannot fulfil a query."""


# ── CMDB ─────────────────────────────────────────────────────────────────────


class CMDBResolverError(ARIABaseError):
    """Raised when CMDB CI class lookup fails and no fallback is possible."""


# ── Notification ────────────────────────────────────────────────────────────


class NotificationError(ARIABaseError):
    """Raised when a Slack or Teams notification cannot be delivered."""
