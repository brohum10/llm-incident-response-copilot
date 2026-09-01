from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request

from .audit import AuditLog
from .copilot import IncidentCopilot, UnsafeIncidentRequest
from .evaluation import run_evaluation
from .providers import provider_from_environment
from .retrieval import HybridRetriever, load_runbooks
from .tools import build_demo_registry


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_copilot() -> IncidentCopilot:
    runbook_directory = Path(os.getenv("RUNBOOK_DIR", PROJECT_ROOT / "runbooks"))
    chunks = load_runbooks(runbook_directory)
    if not chunks:
        raise RuntimeError(f"No runbook chunks found in {runbook_directory}")
    return IncidentCopilot(
        retriever=HybridRetriever(chunks),
        provider=provider_from_environment(),
        tools=build_demo_registry(),
        audit_log=AuditLog(os.getenv("AUDIT_DATABASE", ":memory:")),
    )


def create_app(copilot: IncidentCopilot | None = None) -> Flask:
    app = Flask(__name__)
    app.config["COPILOT"] = copilot or build_copilot()

    @app.get("/v1/health")
    def health():
        service: IncidentCopilot = app.config["COPILOT"]
        return jsonify({"status": "ok", "provider": service.provider.name})

    @app.post("/v1/incidents/analyze")
    def analyze():
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "invalid_request", "message": "JSON body must be an object"}), 400
        description = payload.get("description", "")
        service_name = payload.get("service", "unknown-service")
        try:
            plan = app.config["COPILOT"].analyze(description, service_name)
            return jsonify(plan.to_dict()), 200
        except UnsafeIncidentRequest as exc:
            return jsonify({"error": "unsafe_request", "message": str(exc)}), 422
        except ValueError as exc:
            return jsonify({"error": "invalid_request", "message": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"error": "provider_error", "message": str(exc)}), 502

    @app.get("/v1/incidents/<incident_id>/audit")
    def audit(incident_id: str):
        service: IncidentCopilot = app.config["COPILOT"]
        return jsonify({"incident_id": incident_id, "events": service.audit_log.events_for(incident_id)})

    @app.post("/v1/evaluations/run")
    def evaluate():
        service: IncidentCopilot = app.config["COPILOT"]
        result = run_evaluation(service, PROJECT_ROOT / "evals" / "cases.json")
        return jsonify(result.to_dict()), 200 if result.passed else 503

    return app


app = create_app()
