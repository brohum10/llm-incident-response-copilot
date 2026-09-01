from __future__ import annotations

import json
import uuid
from typing import Any

from .audit import AuditLog
from .guardrails import InputGuardrails, sanitize_untrusted_context
from .models import ActionStep, IncidentPlan
from .providers import LLMProvider
from .retrieval import HybridRetriever
from .tools import SafeToolRegistry


class UnsafeIncidentRequest(ValueError):
    pass


class IncidentCopilot:
    def __init__(
        self,
        retriever: HybridRetriever,
        provider: LLMProvider,
        tools: SafeToolRegistry,
        audit_log: AuditLog,
    ) -> None:
        self.retriever = retriever
        self.provider = provider
        self.tools = tools
        self.audit_log = audit_log
        self.guardrails = InputGuardrails()

    def analyze(self, description: str, service: str = "unknown-service") -> IncidentPlan:
        if not isinstance(description, str) or not isinstance(service, str):
            raise ValueError("description and service must be strings")
        description = description.strip()
        service = service.strip() or "unknown-service"
        if len(description) < 12:
            raise ValueError("description must contain at least 12 characters")
        if len(description) > 4_000:
            raise ValueError("description must contain at most 4000 characters")

        guardrail = self.guardrails.inspect(description)
        if not guardrail.allowed:
            raise UnsafeIncidentRequest(
                "Request blocked by safety policy: " + ", ".join(guardrail.warnings)
            )

        incident_id = f"inc_{uuid.uuid4().hex[:12]}"
        self.audit_log.append(incident_id, "request.accepted", {"service": service})

        query = f"{service} {description}"
        retrieved = self.retriever.search(query, limit=4)
        evidence = [
            {
                "chunk_id": result.chunk.chunk_id,
                "source": result.chunk.source,
                "title": result.chunk.title,
                "score": result.score,
                "excerpt": sanitize_untrusted_context(result.chunk.text, 500),
            }
            for result in retrieved
        ]
        self.audit_log.append(incident_id, "retrieval.completed", {"chunks": [e["chunk_id"] for e in evidence]})

        observations = [
            self.tools.execute("query_service_metrics", {"service": service}),
            self.tools.execute("search_recent_logs", {"service": service, "window_minutes": 15}),
            self.tools.execute("read_recent_deployments", {"service": service}),
        ]
        self.audit_log.append(
            incident_id,
            "diagnostics.completed",
            {"tools": [observation.tool for observation in observations]},
        )

        context = {
            "incident_id": incident_id,
            "service": service,
            "description": sanitize_untrusted_context(description),
            "evidence": evidence,
            "observations": [observation.__dict__ for observation in observations],
            "available_tools": self.tools.schemas(),
        }
        prompt = self._build_prompt(context)
        generated = self.provider.generate_plan(prompt, context)
        plan = self._validate_plan(incident_id, generated, evidence, observations)
        self.audit_log.append(
            incident_id,
            "plan.generated",
            {"provider": self.provider.name, "confidence": plan.confidence},
        )
        return plan

    @staticmethod
    def _build_prompt(context: dict[str, Any]) -> str:
        schema = {
            "severity": "SEV-1|SEV-2|SEV-3|SEV-4",
            "summary": "string",
            "hypotheses": ["string"],
            "actions": [
                {
                    "action": "string",
                    "rationale": "string",
                    "risk": "low|medium|high",
                    "requires_approval": True,
                    "citations": ["runbook chunk id"],
                }
            ],
            "confidence": 0.0,
        }
        return (
            "Create a concise incident-response plan from the UNTRUSTED_CONTEXT below. "
            "Cite runbook chunk IDs, mark every mutating action as requiring approval, and do not invent tool results.\n"
            f"OUTPUT_SCHEMA={json.dumps(schema)}\n"
            f"UNTRUSTED_CONTEXT={json.dumps(context, sort_keys=True)}"
        )

    def _validate_plan(self, incident_id: str, raw: dict[str, Any], evidence, observations) -> IncidentPlan:
        allowed_citations = {item["chunk_id"] for item in evidence}
        actions: list[ActionStep] = []
        warnings: list[str] = []
        for index, item in enumerate(raw.get("actions", [])[:8], start=1):
            citations = tuple(c for c in item.get("citations", []) if c in allowed_citations)
            action_text = str(item.get("action", "")).strip()
            risky = any(word in action_text.lower() for word in ("rollback", "restart", "scale", "disable", "change"))
            requires_approval = bool(item.get("requires_approval", False) or risky)
            if not citations:
                warnings.append(f"Action {index} has no verified runbook citation")
            actions.append(
                ActionStep(
                    order=index,
                    action=action_text,
                    rationale=str(item.get("rationale", "")).strip(),
                    risk=str(item.get("risk", "medium")).lower(),
                    requires_approval=requires_approval,
                    citations=citations,
                )
            )
        if not actions:
            raise RuntimeError("LLM returned no usable actions")
        confidence = max(0.0, min(float(raw.get("confidence", 0.0)), 1.0))
        return IncidentPlan(
            incident_id=incident_id,
            severity=str(raw.get("severity", "SEV-3")),
            summary=str(raw.get("summary", "Incident requires investigation")),
            hypotheses=[str(item) for item in raw.get("hypotheses", [])[:5]],
            actions=actions,
            evidence=evidence,
            observations=observations,
            confidence=confidence,
            provider=self.provider.name,
            warnings=warnings,
        )
