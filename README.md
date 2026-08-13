# ROOOMTECH AIOps

Embedded-first AI operations core for LLM and agent workloads.

## Features

- SQLite/WAL trace storage
- PII and secret redaction before persistence
- Robust MAD latency anomaly detection
- Error fingerprint grouping and deterministic remediation hints
- Latency, token, cost and error metrics
- Prompt version and label registry
- Daily/monthly cost budgets
- Regression comparison by metadata such as prompt or model version
- OTLP JSON trace parser
- No runtime dependencies outside the Python standard library

## Quick start

```python
from aiops.recording import record_span
from aiops.ops import overview, incidents, recommendations

record_span(
    name="answer",
    model="demo-model",
    latency_ms=420,
    cost_usd=0.004,
    metadata={"prompt_version": "v1"},
)

print(overview(60))
print(incidents(60))
print(recommendations(60))
```

Prompt operations:

```python
from aiops.promptops import put_prompt, get_prompt
put_prompt("answer", "Answer concisely", ["production"])
print(get_prompt("answer", "production"))
```

Cost guardrails:

```python
from aiops.costops import set_budget, budget_status
set_budget("monthly", 100.0)
print(budget_status())
```

Regression comparison:

```python
from aiops.ops import compare
print(compare("prompt_version"))
```

OTLP JSON already collected by an OpenTelemetry pipeline can be ingested with `aiops.ops.ingest_otlp(payload)`.

## Positioning

The goal is not to clone every Langfuse screen. The first release focuses on a smaller operational loop: observe, detect, diagnose and recommend. It requires no server, queue, Redis, ClickHouse or external model API for the core workflow.

## Roadmap

- Web dashboard and ingestion API
- Alert delivery to Slack, webhooks and GitHub Actions
- LLM-as-a-judge and dataset experiments
- RBAC and SSO
- ClickHouse/Postgres scale-out storage
- MCP operational interface
- Kubernetes deployment and auto-remediation approval gates

## License

Apache-2.0
