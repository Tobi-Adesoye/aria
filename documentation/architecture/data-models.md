# Data Models

All inter-agent communication uses typed dataclasses defined in `core/models.py`. Agents never pass raw dicts between each other.

---

## AffectedResource

A validated, IP-resolved resource that is the target of investigation. Used wherever ARIA needs to connect to or query a specific host.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | CI / hostname as known in CMDB or extracted from the description |
| `ip_address` | `str \| None` | IP resolved from CMDB — used for SSH/API connections when DNS is unreliable. `None` when CMDB has no IP record or CMDB is unavailable |

`AffectedResource` is a frozen dataclass (immutable). IP comes from CMDB, not from a hosts file, so connections work in any network topology.

---

## IncidentMetadata

Output of Agent 1. Represents a single incident record with all fields needed by downstream agents.

| Field | Type | Description |
|---|---|---|
| `incident_number` | `str` | ITSM ticket identifier (e.g. `INC0012345`) |
| `caller` | `str \| None` | Person who opened the ticket |
| `short_description` | `str` | One-line summary |
| `long_description` | `str` | Full description text |
| `priority` | `Priority` | P1–P4 |
| `state` | `str` | Current ITSM state (New, In Progress, etc.) |
| `affected_ci` | `str \| None` | Primary resolved resource name. `None` when unresolvable (see graceful failure below) |
| `affected_ci_ip` | `str \| None` | IP address of `affected_ci`, resolved from CMDB. Used as SSH/connection target by Agent 2 |
| `ci_class` | `CIClass \| None` | Resolved CI type: `service`, `node`, `cluster`, `unknown` |
| `affected_resources` | `list[AffectedResource]` | Validated resources extracted from description + confirmed via CMDB/KB, each carrying an IP address. Single resource → `affected_ci` is also set. Multiple resources → `affected_ci` is `None` |
| `assigned_group` | `str \| None` | OPS team assigned |
| `opened_at` | `datetime` | When the incident was raised |
| `platform_tag` | `PlatformTag \| None` | Set by Agent 1; drives Agent 2 connector routing |
| `raw_record` | `dict` | Full raw response from the ITSM connector. Agent 1 also writes `_cluster_resolution` and `_llm_extraction` keys here for diagnostics |

### Graceful failure contract

When Agent 1 cannot resolve a cluster to a specific resource, it sets `affected_ci = None` and `affected_resources = []`. Agent 2 detects this and sets `state.error` with a descriptive message. The error propagates unchanged through every downstream agent until it reaches the communication system (Agent 4), which reports it.

This is the correct M3 behaviour for cluster incidents without a configured Knowledge Base. KB-backed resolution is added in M3.5.

### CIClass enum

```python
class CIClass(str, Enum):
    SERVICE = "service"
    NODE    = "node"
    CLUSTER = "cluster"
    UNKNOWN = "unknown"
```

Drives Agent 1's three-path resolution logic. Agent 1 sets this field after querying the CMDB or inferring from the description.

---

## LogAccessHint

Returned by `KnowledgeBaseInterface.get_log_hints()`. Tells Agent 2 where to look for logs for a given service.

| Field | Type | Description |
|---|---|---|
| `platform_tag` | `PlatformTag` | Platform the service runs on |
| `log_paths` | `list[str]` | Known log file paths or query expressions |
| `keywords` | `list[str]` | Relevant error keywords to filter on |
| `aggregator_endpoint` | `str \| None` | Splunk/ELK endpoint if a centralised aggregator is known |
| `confidence` | `float` | How closely the KB entry matched the query (0.0–1.0) |

---

## LogQueryResult

Output of Agent 2.

| Field | Type | Description |
|---|---|---|
| `log_lines` | `list[LogLine]` | Retrieved log entries |
| `query_executed` | `str` | The actual query or glob pattern used |
| `total_scanned` | `int` | Number of log entries examined |
| `confidence` | `ConfidenceBand` | `high / medium / low` |

### LogLine

A single parsed log entry: `timestamp`, `level`, `message`, `source`.

---

## ClassificationResult

Output of Agent 3.

| Field | Type | Description |
|---|---|---|
| `error_class` | `str` | Machine-readable label: `OOM`, `disk`, `network`, etc. |
| `error_label` | `str` | Human-readable description |
| `confidence` | `float` | Raw confidence score (0.0–1.0) |
| `confidence_band` | `ConfidenceBand` | `high / medium / low` — mandatory in all notifications |
| `supporting_evidence` | `list[str]` | Log lines or patterns that drove the classification |
| `recommended_actions` | `list[str]` | Suggested remediation steps |

---

## PipelineState

The shared state object passed through every LangGraph node.

| Field | Type | Description |
|---|---|---|
| `incident_number` | `str` | The trigger — set at pipeline start |
| `incident_metadata` | `IncidentMetadata \| None` | Set by Agent 1 |
| `log_result` | `LogQueryResult \| None` | Set by Agent 2 |
| `classification` | `ClassificationResult \| None` | Set by Agent 3 |
| `approval_status` | `ApprovalStatus \| None` | Reserved for Phase 2 human gate |
| `notification_sent` | `bool` | Set by Agent 4 |
| `error` | `str \| None` | Set if any node fails — pipeline aborts cleanly |

---

## Enums

### Priority

```python
class Priority(str, Enum):
    P1 = "P1"   # Critical
    P2 = "P2"   # High
    P3 = "P3"   # Medium
    P4 = "P4"   # Low
```

### PlatformTag

```python
class PlatformTag(str, Enum):
    CDP         = "cdp"
    DATABRICKS  = "databricks"
    ORACLE      = "oracle"
    GCP         = "gcp"
    AWS         = "aws"
    AZURE       = "azure"
    KAFKA       = "kafka"
    UNKNOWN     = "unknown"
```

Used by Agent 2 to route to the correct log connector.

### ConfidenceBand

```python
class ConfidenceBand(str, Enum):
    HIGH   = "high"    # confidence >= 0.7
    MEDIUM = "medium"  # 0.5 – 0.69
    LOW    = "low"     # < 0.5
```
