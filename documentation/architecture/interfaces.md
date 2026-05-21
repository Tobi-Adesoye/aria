# Interfaces & Plugin System

All external dependencies in ARIA are defined as Python Abstract Base Classes (ABCs) in `core/interfaces/`. Agents interact with these ABCs only — they never import a concrete implementation directly.

This means:

- **Tests** use in-memory stubs with no network or credentials
- **Production** deployments inject real implementations via dependency injection
- **Third-party contributors** add connectors without touching agent code

---

## ConnectorInterface

**File**: `core/interfaces/connector.py`

The contract for ITSM connectors. Currently implemented by `ServiceNowConnector`.

```python
class ConnectorInterface(ABC):
    def get_incident(self, incident_number: str) -> dict: ...
```

The connector returns the raw incident record. Parsing and structuring is done by Agent 1, not the connector — connectors are intentionally thin.

**Exceptions**: `IncidentNotFoundError` (404), `ConnectorAuthError` (401/403), `ConnectorUnavailableError` (network/timeout).

---

## LogStoreInterface

**File**: `core/interfaces/log_store.py`

The contract for log store connectors. Agent 2 calls this to retrieve log lines for a service within a time window.

```python
class LogStoreInterface(ABC):
    def query_logs(
        self,
        host: str,
        platform_tag: PlatformTag,
        start_time: datetime,
        end_time: datetime,
        keywords: list[str] | None = None,
        log_paths: list[str] | None = None,
        max_results: int = 50,
    ) -> LogQueryResult: ...
```

`keywords` and `log_paths` are optional — populated from `KnowledgeBaseInterface.get_log_hints()` when available. Connectors that don't need them (e.g. `InMemoryLogStore`) ignore them. Connectors that do (CDP, GCP) use them for targeted queries.

**Implementations (M3)**:
- `SSHLogConnector` (`clusters/onprem/`) — SSH grep for any on-premise cluster (CDP, HDP, MapR, Oracle RAC, etc.); log dirs and credentials configured at construction time
- `GCPLogConnector` (`clusters/cloud/gcp/`) — Cloud Logging API filter query
- `InMemoryLogStore` — fixture-backed, for unit tests

**Cloud connector stubs (M3.5)**:
- `clusters/cloud/aws/` — AWS EMR, S3 log bucket via boto3
- `clusters/cloud/databricks/` — Databricks DBFS / cloud storage API
- `clusters/cloud/azure/` — Azure Monitor Log Analytics workspace

**Exceptions**: `LogQueryTimeoutError`, `LogStoreUnavailableError`.

---

## VaultInterface

**File**: `core/interfaces/vault.py`

The contract for secret/credential stores. Agents retrieve credentials by key name — never by hardcoding values.

```python
class VaultInterface(ABC):
    def get_secret(self, key: str) -> str: ...
```

**Reference implementation**: `EnvVarVault` (`implementations/vault/envvar.py`) reads from environment variables. Supports an optional `prefix` parameter to namespace keys (e.g. `prefix="ARIA_"` maps `get_secret("CDP_KEY")` to env var `ARIA_CDP_KEY`).

**Production**: Replace with a HashiCorp Vault or cloud secrets manager implementation. The agents are unaware of the change.

**Exceptions**: `VaultSecretNotFoundError`, `VaultUnavailableError`.

---

## KnowledgeBaseInterface

**File**: `core/interfaces/knowledge_base.py`

Dual-use interface queried by both Agent 1 and Agent 2.

```python
class KnowledgeBaseInterface(ABC):
    def get_service_hints(self, cluster: str, description: str) -> list[str]: ...
    def get_log_hints(self, service: str, platform_tag: PlatformTag) -> LogAccessHint: ...
```

- **Agent 1** calls `get_service_hints()` during cluster→service resolution to get candidate service names.
- **Agent 2** calls `get_log_hints()` as a fallback when the primary log connector returns no results.

Both methods return empty results (not raise) when no entry exists — errors are reserved for backend unavailability.

**Reference implementation**: `FileKnowledgeBase` (`implementations/knowledge_base/file_kb.py`) — loads `.md`/`.txt` runbook files from a directory, scores by token overlap, extracts log paths and keywords via regex. No network or vector DB required — suitable for unit tests and local dev.

**Exceptions**: `KnowledgeBaseError` (backend unreachable only).

---

## CMDBResolver

**File**: `core/cmdb_resolver.py`

Not an ABC — a concrete ServiceNow-specific helper used by Agent 1 for three-path CI resolution. All methods are non-fatal: exceptions are caught, a `WARNING` is logged, and a safe default is returned. The pipeline always continues.

```python
class CMDBResolver:
    def get_ci_class(self, ci_name: str) -> CIClass: ...
    # Returns UNKNOWN on miss or error.

    def get_ip(self, ci_name: str) -> Optional[str]: ...
    # Returns the IP address from cmdb_ci.ip_address. None on miss or error.

    def get_parent_cluster(self, ci_name: str) -> Optional[str]: ...
    # Returns the cluster name that contains this CI as a member. None if not found.

    def is_member(self, cluster_name: str, ci_name: str) -> bool: ...
    # Returns True if ci_name is a direct member of cluster_name. False on error.

    def resolve(self, cluster_name: str) -> list[AffectedResource]: ...
    # Returns member nodes with IPs for a cluster CI. [] on miss or error.
    # Each AffectedResource carries the node name and its IP from CMDB.
```

The relationship type used for membership queries is configurable via `SNOW_CMDB_REL_TYPE` environment variable (default: `Members::Member of`).

Instantiate via `CMDBResolver.from_env()` in production (reads `SNOW_INSTANCE`, `SNOW_USER`, `SNOW_PASSWORD`, `SNOW_CMDB_REL_TYPE`) or inject directly in tests.

---

## LLMClientInterface

**File**: `core/interfaces/llm_client.py`

The contract for LLM providers. Both Agent 1 (extraction) and Agent 3 (classification) call this.

```python
class LLMClientInterface(ABC):
    def complete(self, prompt: str, system: str | None = None) -> str: ...
```

**Reference implementation**: `AnthropicLLMClient` (`implementations/llm/anthropic/llm_client.py`) — uses Claude. The model name is injected via environment variable (`ARIA_AGENT1_MODEL`, `ARIA_AGENT3_MODEL`), so adopters can swap models without code changes.

**Exceptions**: `LLMAuthError`, `LLMUnavailableError`, `LLMResponseError`.

---

## QueueInterface

**File**: `core/interfaces/queue.py`

The contract for the incident trigger queue. The orchestrator consumes incident numbers from this queue to start pipeline runs.

---

## StateStoreInterface

**File**: `core/interfaces/state_store.py`

The contract for persisting `PipelineState` between runs. Used for auditability and recovery — if a run fails mid-pipeline, the state can be inspected.
