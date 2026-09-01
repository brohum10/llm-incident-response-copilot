# High Latency Runbook

## Triage
Identify which endpoint and dependency dominate p95 and p99 latency. Compare request volume, saturation, error rate, and recent deployments before changing capacity.

## Dependency analysis
Use distributed traces and redacted logs to separate application processing time from database, cache, and downstream HTTP time. Preserve a representative trace ID for follow-up.

## Recovery
Prefer reversible mitigations. Rollbacks, restarts, scaling changes, and feature-flag changes require an authorized human operator. Verify recovery using user-facing service-level indicators.

