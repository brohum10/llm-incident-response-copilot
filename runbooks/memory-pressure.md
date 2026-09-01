# Memory Pressure Runbook

## Detection
Memory pressure appears as rising resident memory, increased garbage-collection pauses, allocation failures, container restarts, or out-of-memory events.

## Investigation
Compare memory growth with request rate and deployment changes. Capture heap usage, garbage-collection pause time, container limits, and the largest allocation classes without collecting sensitive request payloads.

## Mitigation
A rollback is preferred for deployment-correlated leaks. Restarting can restore service temporarily but requires approval and does not fix the root cause. Preserve diagnostic evidence before any restart.

