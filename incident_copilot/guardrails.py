from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    warnings: tuple[str, ...]


class InputGuardrails:
    """Blocks common prompt-injection and destructive-operation requests."""

    _patterns = {
        "prompt injection": re.compile(
            r"(ignore|forget|override).{0,30}(instruction|system|policy)|reveal.{0,20}(prompt|secret)",
            re.IGNORECASE,
        ),
        "destructive operation": re.compile(
            r"\b(drop\s+(table|database)|rm\s+-rf|delete\s+all|wipe\s+(the\s+)?database|shutdown\s+-h)\b",
            re.IGNORECASE,
        ),
        "credential request": re.compile(
            r"\b(print|show|dump|reveal|return).{0,25}(api[_ -]?key|password|token|credential|secret)\b",
            re.IGNORECASE,
        ),
    }

    def inspect(self, text: str) -> GuardrailResult:
        warnings = tuple(name for name, pattern in self._patterns.items() if pattern.search(text))
        return GuardrailResult(allowed=not warnings, warnings=warnings)


def sanitize_untrusted_context(text: str, max_chars: int = 2_000) -> str:
    """Treat logs and runbooks as data and strip control-like XML markers."""
    cleaned = re.sub(r"</?(system|assistant|developer|tool)[^>]*>", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "'''" )
    return cleaned[:max_chars]

