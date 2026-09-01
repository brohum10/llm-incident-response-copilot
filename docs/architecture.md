# Architecture and design decisions

## Goal

The copilot reduces the time needed to assemble an evidence-based incident plan without giving a probabilistic model direct control of production systems. The key design choice is to separate retrieval, diagnostics, generation, validation, and execution authority.

## Components

### Retrieval layer

Runbooks are split at second-level Markdown headings so citations identify a useful operational unit rather than an entire file. BM25 provides transparent lexical ranking. A small synonym-expansion layer improves recall for incident vocabulary such as latency, saturation, memory pressure, and error rate without requiring an embedding model download.

### Diagnostic tool boundary

`SafeToolRegistry` accepts only definitions marked read-only. The sample tools return metrics, redacted log signatures, and deployment metadata. A production adapter would connect these definitions to observability APIs while preserving the same narrow interface.

### Provider boundary

`LLMProvider` has one responsibility: generate a structured plan from a prompt and context. The deterministic provider makes CI and demos reproducible. The network provider uses an OpenAI-compatible chat-completions endpoint and requests a JSON object.

### Validation layer

The model cannot decide whether its own output is trustworthy. The validator:

1. limits plans to eight actions;
2. removes citations not returned by retrieval;
3. adds warnings for uncited actions;
4. clamps confidence to `[0, 1]`;
5. forces approval for potentially mutating actions;
6. rejects responses with no usable actions.

### Audit layer

SQLite records accepted requests, retrieved chunk IDs, tools invoked, provider name, and final confidence. Request bodies, API keys, and full log payloads are deliberately excluded. A lock protects the shared connection in the threaded web server.

## Trust boundaries

```text
untrusted: user description, logs, runbooks, model output
trusted:   static system policy, tool allowlist, citation validator, approval rules
external:  LLM endpoint and future observability providers
```

Untrusted context is size-limited and stripped of role-like XML tags and code fences before prompt assembly. This is defense in depth; production deployments should also use model-provider controls and organization-specific content filtering.

## Failure behavior

- Invalid input returns `400`.
- Prompt injection, destructive requests, and credential-seeking requests return `422`.
- Provider or response-validation failures return `502`.
- Retrieval can return no evidence, but uncited actions are visibly warned rather than silently presented as grounded.
- The service never converts a model recommendation into an operational write.

## Production extensions

- Replace local Markdown retrieval with versioned runbooks in a vector and lexical index.
- Add SSO-backed approval objects with expiry, approver identity, and separation of duties.
- Connect read-only adapters to metrics, tracing, logs, deployment history, and feature flags.
- Add secret and PII redaction before storage or model calls.
- Add provider timeouts, retries with jitter, circuit breakers, budgets, and model fallbacks.
- Evaluate retrieval and plan quality against resolved incident retrospectives with human scoring.
- Export audit events and latency/cost metrics through OpenTelemetry.

