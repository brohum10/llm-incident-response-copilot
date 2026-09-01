from pathlib import Path

import pytest

from incident_copilot.audit import AuditLog
from incident_copilot.copilot import IncidentCopilot
from incident_copilot.providers import DemoLLMProvider
from incident_copilot.retrieval import HybridRetriever, load_runbooks
from incident_copilot.tools import build_demo_registry


ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def copilot():
    return IncidentCopilot(
        retriever=HybridRetriever(load_runbooks(ROOT / "runbooks")),
        provider=DemoLLMProvider(),
        tools=build_demo_registry(),
        audit_log=AuditLog(),
    )

