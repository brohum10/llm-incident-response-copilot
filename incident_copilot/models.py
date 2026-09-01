from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RunbookChunk:
    chunk_id: str
    source: str
    title: str
    text: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: RunbookChunk
    score: float


@dataclass(frozen=True)
class ToolObservation:
    tool: str
    summary: str
    data: dict[str, Any]


@dataclass(frozen=True)
class ActionStep:
    order: int
    action: str
    rationale: str
    risk: str
    requires_approval: bool
    citations: tuple[str, ...] = ()


@dataclass
class IncidentPlan:
    incident_id: str
    severity: str
    summary: str
    hypotheses: list[str]
    actions: list[ActionStep]
    evidence: list[dict[str, Any]]
    observations: list[ToolObservation]
    confidence: float
    provider: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

