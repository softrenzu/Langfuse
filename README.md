# RooomObserve — LLM & Agent Operations

Version: `0.3.0`

RooomObserve is a source-available, embedded-first operations core for LLM and agent workloads. It focuses on a compact operational loop: observe, detect, diagnose, compare, and recommend.

## Core features

- SQLite/WAL trace storage
- PII and secret redaction before persistence
- Robust MAD latency anomaly detection
- Error fingerprint grouping and deterministic remediation hints
- Latency, token, cost, and error metrics
- Prompt version and label registry
- Daily and monthly cost budgets
- Regression comparison by prompt/model metadata
- OTLP JSON trace parsing
- No runtime dependencies outside the Python standard library

The existing `aiops` Python import namespace is retained for compatibility in the `0.3.x` line; the product name is RooomObserve.

## Example

```python
from aiops.recording import record_span
from aiops.ops import overview, incidents, recommendations

record_span(name="answer", model="demo-model", latency_ms=420, cost_usd=0.004)
print(overview(60))
print(incidents(60))
print(recommendations(60))
```

## Roadmap

- Web dashboard and ingestion API
- Alert delivery
- LLM-as-a-judge and dataset experiments
- RBAC and SSO
- Scale-out storage
- MCP operational interface
- Kubernetes deployment and approval-gated remediation

## Licensing and enterprise support

Starting with version `0.3.0`, ROOOMTECH-authored code is available under the terms described in `LICENSE`: PolyForm Noncommercial License 1.0.0 for permitted noncommercial uses, or a separate paid ROOOMTECH Commercial Software License for business/commercial-purpose uses outside those permissions.

Commercial license agreements, maintenance, support, implementation, integration, upgrades, security support, SLA options, private builds, and custom development are available.

Contact: `support@rooomtech.com`

Earlier releases retain their published license terms. Third-party software retains its own licenses.
