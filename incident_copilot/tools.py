from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .models import ToolObservation


ToolHandler = Callable[[dict[str, Any]], ToolObservation]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    read_only: bool
    handler: ToolHandler


class SafeToolRegistry:
    """Runs only explicitly registered, read-only diagnostic tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if not definition.read_only:
            raise ValueError("Only read-only tools can be registered")
        self._tools[definition.name] = definition

    def schemas(self) -> list[dict[str, str]]:
        return [
            {"name": tool.name, "description": tool.description, "mode": "read-only"}
            for tool in sorted(self._tools.values(), key=lambda item: item.name)
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolObservation:
        if name not in self._tools:
            raise ValueError(f"Tool is not allowlisted: {name}")
        return self._tools[name].handler(arguments)


def build_demo_registry() -> SafeToolRegistry:
    registry = SafeToolRegistry()
    registry.register(
        ToolDefinition(
            name="query_service_metrics",
            description="Read recent latency, error-rate, traffic, and saturation metrics.",
            read_only=True,
            handler=lambda args: ToolObservation(
                tool="query_service_metrics",
                summary="Checkout API latency and database saturation are elevated.",
                data={
                    "service": args.get("service", "checkout-api"),
                    "p95_latency_ms": 1_840,
                    "error_rate": 0.073,
                    "requests_per_second": 421,
                    "db_pool_utilization": 0.96,
                },
            ),
        )
    )
    registry.register(
        ToolDefinition(
            name="search_recent_logs",
            description="Search redacted application logs for recurring failure signatures.",
            read_only=True,
            handler=lambda args: ToolObservation(
                tool="search_recent_logs",
                summary="Database connection acquisition timeouts dominate recent errors.",
                data={
                    "service": args.get("service", "checkout-api"),
                    "matches": 183,
                    "signature": "SQLTransientConnectionException: connection is not available",
                    "window_minutes": min(int(args.get("window_minutes", 15)), 60),
                },
            ),
        )
    )
    registry.register(
        ToolDefinition(
            name="read_recent_deployments",
            description="Read deployment metadata for correlation; does not roll back or mutate services.",
            read_only=True,
            handler=lambda args: ToolObservation(
                tool="read_recent_deployments",
                summary="Version 2026.09.01-3 deployed shortly before the incident.",
                data={
                    "service": args.get("service", "checkout-api"),
                    "version": "2026.09.01-3",
                    "minutes_before_incident": 11,
                    "changes": ["checkout tracing", "database client timeout defaults"],
                },
            ),
        )
    )
    return registry

