# Contributing to LLM Incident Response Copilot

Contributions should keep generated guidance grounded, auditable, and human-controlled.

## Local checks

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest --cov=incident_copilot --cov-report=term-missing
python -m incident_copilot.evaluation
python -m build
```

The deterministic provider is the default for tests. Contributions must not require a paid model or API key to verify core behavior.

## Expectations

- Treat incident text, logs, runbooks, and model output as untrusted data.
- Keep mutating operations approval-gated and diagnostic tools explicitly allowlisted.
- Reject or surface invalid citations instead of silently accepting them.
- Add an evaluation case for retrieval, grounding, or safety-policy changes.
- Update the OpenAPI and architecture documents when contracts or trust boundaries change.

Pull requests should explain the threat model, evaluation impact, tests run, and any model-specific behavior.
