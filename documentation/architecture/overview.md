# Architecture Overview

## Design philosophy

ARIA is built around a **plugin architecture** with a cloud-agnostic core. The guiding constraint is that many target environments are on-premise: a system that couples tightly to GCP or AWS services cannot be deployed at a Cloudera CDP site.

Every external dependency (ITSM connector, log store, secret store, queue, LLM provider) is hidden behind an Abstract Base Class (ABC). The core agents interact with these ABCs only — they never instantiate concrete implementations directly. Swapping a connector is a config change, not a code change.

## High-level data flow

```
ServiceNow ──► Agent 1 (Incident Reader)
                    │
                    ▼
              IncidentMetadata
                    │
                    ▼
              Agent 2 (Log Finder) ◄── KnowledgeBase (log hints)
                    │
                    ▼
              LogQueryResult
                    │
                    ▼
              Agent 3 (Classifier) ◄── LLM (Claude)
                    │
                    ▼
           ClassificationResult
                    │
                    ▼
              Agent 4 (Notifier) ──► Slack / MS Teams
```

Agents are composed into a **LangGraph pipeline**. Each agent is a graph node. The shared `PipelineState` object is passed through every node in sequence.

## Orchestration: LangGraph

LangGraph manages the execution graph, state passing, and retry logic between nodes. Agents 2 and 3 form a **ReAct loop**: the classifier can request additional log context, which triggers another log query before producing a final classification.

The loop runs in-memory within the same process — no external queue is needed for the inner loop. The outer queue (incident triggers → pipeline) is the only cross-process boundary in Phase 1.

## Key architectural decisions

### ABCs for every external dependency

All I/O dependencies are defined as Python ABCs in `core/interfaces/`. This means:

- Unit tests use in-memory stubs — no network required
- Production deployments swap implementations via dependency injection
- Third-party contributors can add connectors without touching agent code

### LLM extraction in Agent 1

ServiceNow incident descriptions are often free-text and inconsistently filled. Rather than brittle regex, Agent 1 uses an LLM call to extract structured fields (`affected_ci`, `platform_tag`, scope) from the raw description. The LLM output is validated against the `IncidentMetadata` model. If extraction fails, Agent 1 surfaces the raw fields and logs a warning — it never raises.

### Three-path CI resolution in Agent 1

The `affected_ci` field in a ServiceNow ticket can point to a cluster, a specific service/node, or be absent entirely. Agent 1 handles all three cases:

1. **CI is a known service** — pass through directly
2. **CI is a cluster** — use `KnowledgeBaseInterface.get_service_hints()` to narrow down to a specific service, then confirm with LLM
3. **CI is absent** — derive from incident description text alone, fall back to `CIClass.UNKNOWN`

### Secret management

No secrets are stored in agent code or config files. All credentials are retrieved via `VaultInterface.get_secret(key)`. The reference implementation (`EnvVarVault`) reads from environment variables. Production deployments replace it with a HashiCorp Vault or cloud secrets manager implementation — the agents are unaware of the change.

## Module layout

```
aria/
├── core/
│   ├── agents/          # Agent implementations (pure business logic)
│   ├── interfaces/      # ABCs for all external dependencies
│   ├── models.py        # Shared data models (IncidentMetadata, etc.)
│   └── exceptions.py    # Domain-specific exceptions
├── implementations/
│   ├── clusters/
│   │   ├── onprem/      # SSHLogConnector — any bare-metal/VM cluster (CDP, HDP, MapR, Oracle, etc.)
│   │   └── cloud/       # Cloud-native connectors (gcp/, aws/, databricks/, azure/)
│   ├── coms/            # Communication stubs (slack/, teams/)
│   ├── itsm/            # ITSM connectors (servicenow/)
│   ├── knowledge_base/  # FileKnowledgeBase and future vector DB implementations
│   ├── llm/             # LLM clients (anthropic/)
│   ├── memory/          # In-memory stubs for testing
│   └── vault/           # Secret store implementations (envvar.py)
├── api/                 # FastAPI REST layer (Agent 1 endpoint)
├── tests/
│   ├── unit/            # No network, no credentials required
│   └── integration/     # Require real external services
└── documentation/       # This site
```
