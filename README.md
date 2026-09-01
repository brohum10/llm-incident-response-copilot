# LLM Incident Response Copilot

[![CI](https://github.com/brohum10/llm-incident-response-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/brohum10/llm-incident-response-copilot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB)](https://www.python.org/)
[![Safety: approval gated](https://img.shields.io/badge/actions-approval--gated-0A7B83)](#safety-model)

A retrieval-augmented LLM service that turns noisy production incidents into cited, auditable response plans. It retrieves relevant runbook sections, gathers evidence through allowlisted read-only tools, asks an LLM for a structured plan, validates every citation, and forces human approval for mutating actions.

The project runs locally in deterministic demo mode with no API key. A real OpenAI-compatible model can be enabled with environment variables.

## Why this is more than a chatbot

- **Hybrid retrieval:** BM25 ranking plus incident-domain query expansion over chunked Markdown runbooks.
- **Plan → validate → audit workflow:** model output is parsed into a typed incident plan and checked before it reaches the API.
- **Tool safety:** only registered read-only diagnostics can execute; restarts, rollbacks, scaling, and configuration changes are never automated.
- **Grounded output:** action citations must match retrieved runbook chunk IDs. Unknown citations are removed and surfaced as warnings.
- **Prompt-injection defense:** incident text, logs, and runbooks are treated as untrusted data; destructive or credential-seeking requests are blocked.
- **Deterministic evaluation:** six cases measure retrieval Recall@4, citation coverage, unsafe-request blocking, and local latency.
- **Operational traceability:** each request, retrieval, diagnostic call, and generated plan is recorded in a thread-safe SQLite audit log.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m incident_copilot
```

The service starts on `http://localhost:8080` in offline demo mode.

```bash
curl -X POST http://localhost:8080/v1/incidents/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "service": "checkout-api",
    "description": "Checkout p95 latency is 1.8 seconds and the database pool is saturated after a deploy."
  }'
```

The response includes severity, hypotheses, read-only diagnostic observations, a risk-labeled action plan, verified runbook citations, confidence, and safety warnings.

## Use a real LLM

The provider speaks the common chat-completions JSON protocol and works with OpenAI-compatible endpoints.

```bash
export LLM_API_KEY='your-key'
export LLM_MODEL='gpt-4.1-mini'
export LLM_BASE_URL='https://api.openai.com/v1'
python -m incident_copilot
```

Keys are read only from the environment and are never written to prompts, audit events, or responses. Demo mode remains the default so tests and reviewers do not need credentials.

## Architecture

```text
Incident request
      │
      ▼
Input guardrails ── blocked ──> 422 safety response
      │ allowed
      ├──> Hybrid runbook retrieval ──> cited evidence
      ├──> Read-only tool registry ───> metrics / logs / deployments
      │
      ▼
Prompt assembler ──> LLM provider ──> plan validator
                                         │
                           verified citations + approval gates
                                         │
                                         ▼
                                API response + audit log
```

See [docs/architecture.md](docs/architecture.md) for component boundaries, trust zones, failure behavior, and production extensions.

## API

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/health` | Report service and provider status |
| `POST` | `/v1/incidents/analyze` | Generate a cited incident-response plan |
| `GET` | `/v1/incidents/{id}/audit` | Read the incident's append-only audit trail |
| `POST` | `/v1/evaluations/run` | Run the deterministic safety and retrieval evaluation |

## Tests and evaluation

```bash
pytest -q
pytest --cov=incident_copilot --cov-report=term-missing
curl -X POST http://localhost:8080/v1/evaluations/run
```

The evaluation gate passes only when:

- retrieval Recall@4 is at least `0.80`;
- citation coverage is at least `0.90`;
- unsafe-request block rate is exactly `1.00`.

Latest deterministic demo evaluation (September 1, 2026):

| Cases | Recall@4 | Citation coverage | Unsafe block rate |
|---:|---:|---:|---:|
| 6 | 1.00 | 1.00 | 1.00 |

These are local evaluation results over the checked-in synthetic cases, not claims about production incident resolution.

## Safety model

This service recommends actions; it does not execute operational changes. Diagnostic tools are explicitly allowlisted and read-only. Any generated action containing rollback, restart, scale, disable, or change semantics is automatically marked `requires_approval=true`, even if the model says otherwise.

Before production use, add identity-aware approval workflows, per-tenant data isolation, secret redaction, a production retrieval store, provider retry/circuit-breaking, and organization-specific incident policies.

## Docker

```bash
docker compose up --build
```

## License

MIT

