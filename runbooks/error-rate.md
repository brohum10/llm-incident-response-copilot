# Elevated Error Rate Runbook

## Triage
Break down failures by endpoint, status code, availability zone, version, and dependency. Compare the start time with deployments, configuration changes, and traffic anomalies.

## Investigation
Cluster redacted logs by exception signature and examine representative traces. Validate whether retries are amplifying load. Never copy secrets or customer payloads into the incident timeline.

## Recovery
Choose the smallest reversible mitigation that addresses the leading hypothesis. Any rollback, traffic shift, or feature disablement requires explicit approval and post-change verification.

