"""Pydantic request/response models for the ARIA REST API.

All agent endpoints share the same envelope:
  { status, agent, incident_number, duration_ms, data, error }

The `data` field is agent-specific and typed per router.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# ── Shared envelope ────────────────────────────────────────────────────────────


class AgentResponse(BaseModel):
    status: str  # "success" | "error"
    agent: str
    incident_number: str
    duration_ms: int
    data: Optional[Any] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    agent: str
    incident_number: str
    duration_ms: int
    data: None = None
    error: str


# ── Agent 1 ────────────────────────────────────────────────────────────────────


class Agent1RunRequest(BaseModel):
    incident_number: str


class LLMExtractionDetail(BaseModel):
    affected_ci: Optional[str]
    platform_tag: str
    confidence: str


class IncidentData(BaseModel):
    incident_number: str
    caller: Optional[str]
    short_description: str
    long_description: str
    priority: str
    state: str
    affected_ci: Optional[str]
    assigned_group: Optional[str]
    opened_at: datetime
    llm_extraction: Optional[LLMExtractionDetail] = None


class Agent1Response(AgentResponse):
    agent: str = "agent1"
    data: Optional[IncidentData] = None


# ── Agent 1 health ─────────────────────────────────────────────────────────────


class AgentHealthResponse(BaseModel):
    agent: str
    status: str  # "ready" | "degraded" | "unavailable"
    llm_model: Optional[str] = None
    connector: Optional[str] = None


# ── Agent 2 ────────────────────────────────────────────────────────────────────


class AffectedResourceInput(BaseModel):
    name: str
    ip_address: Optional[str] = None


class Agent2MetadataInput(BaseModel):
    """Pre-fetched incident metadata for Agent 2 — skips calling Agent 1."""

    affected_ci: Optional[str] = None
    affected_ci_ip: Optional[str] = None
    platform_tag: str = "unknown"
    opened_at: datetime
    affected_resources: List[AffectedResourceInput] = []


class Agent2RunRequest(BaseModel):
    incident_number: str
    metadata: Optional[Agent2MetadataInput] = None  # if None → Agent 1 called first


class LogLineData(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str


class LogQueryPlanData(BaseModel):
    """LLM-generated query plan produced by Agent 2 (S5.5 — ARI-78).

    Null in the response when ARIA_AGENT2_MODEL is not set (static routing used).
    """

    connector_name: str
    log_paths: List[str]
    keywords: List[str]
    time_window_minutes: int
    reasoning: str


class Agent2Data(BaseModel):
    query_executed: str
    total_scanned: int
    confidence: str  # "high" | "medium" | "low"
    log_lines: List[LogLineData]
    log_query_plan: Optional[LogQueryPlanData] = None


class Agent2Response(AgentResponse):
    agent: str = "agent2"
    data: Optional[Agent2Data] = None


# ── Agent 4 ────────────────────────────────────────────────────────────────────


class Agent4ClassificationInput(BaseModel):
    """Optional pre-built classification — skips Agent 3 for standalone testing."""

    error_class: str
    error_label: str
    confidence: float
    confidence_band: str  # "high" | "medium" | "low"
    supporting_evidence: List[str] = []
    recommended_actions: List[str] = []


class Agent4RunRequest(BaseModel):
    incident_number: str
    classification: Optional[Agent4ClassificationInput] = None


class Agent4Data(BaseModel):
    notification_sent: bool
    channel: str  # e.g. "slack"
    message_id: Optional[str] = None
    is_partial: bool


class Agent4Response(AgentResponse):
    agent: str = "agent4"
    data: Optional[Agent4Data] = None


# ── Global health ──────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    agents: Dict[str, str]
