import pytest

from incident_copilot.audit import AuditLog
from incident_copilot.models import ToolObservation
from incident_copilot.tools import SafeToolRegistry, ToolDefinition, build_demo_registry


def test_demo_tools_return_structured_observations():
    registry = build_demo_registry()
    observation = registry.execute("query_service_metrics", {"service": "api"})
    assert observation.tool == "query_service_metrics"
    assert observation.data["service"] == "api"
    assert observation.data["p95_latency_ms"] > 1_000


def test_registry_rejects_mutating_tools():
    registry = SafeToolRegistry()
    with pytest.raises(ValueError, match="read-only"):
        registry.register(
            ToolDefinition("restart_service", "restart", False, lambda _: ToolObservation("x", "x", {}))
        )


def test_registry_rejects_unknown_tool():
    with pytest.raises(ValueError, match="not allowlisted"):
        build_demo_registry().execute("delete_database", {})


def test_tool_schemas_are_sorted_and_marked_read_only():
    schemas = build_demo_registry().schemas()
    assert [schema["name"] for schema in schemas] == sorted(schema["name"] for schema in schemas)
    assert all(schema["mode"] == "read-only" for schema in schemas)


def test_audit_log_preserves_event_order():
    with AuditLog() as audit:
        audit.append("inc_1", "first", {"value": 1})
        audit.append("inc_1", "second", {"value": 2})
        events = audit.events_for("inc_1")
    assert [event["event_type"] for event in events] == ["first", "second"]
    assert events[1]["payload"] == {"value": 2}
