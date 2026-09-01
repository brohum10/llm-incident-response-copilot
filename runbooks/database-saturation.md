# Database Saturation Runbook

## Detection
Database saturation commonly appears as elevated request latency, connection-acquisition timeouts, and pool utilization above 90%. Compare application error rate with database active connections and queue depth.

## Investigation
Capture p50 and p95 latency, error rate, pool utilization, slow queries, active connections, and deployment timestamps. Search logs for connection timeout signatures. Do not expose query parameters or credentials in the incident record.

## Mitigation
If impact begins immediately after a deployment, prepare a rollback and require human approval before execution. If traffic increased organically, consider approved temporary scaling and traffic shaping. Do not increase pool size without checking database connection limits.

## Verification
Confirm error rate, p95 latency, pool utilization, and queue depth return to baseline for at least ten minutes. Record the exact mitigation and attach supporting metrics.

