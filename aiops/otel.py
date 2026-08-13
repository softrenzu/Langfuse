from __future__ import annotations

import time
from typing import Any


def _attrs(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items or []:
        key = item.get("key")
        value = item.get("value", {})
        if not key:
            continue
        for field in ("stringValue", "intValue", "doubleValue", "boolValue"):
            if field in value:
                out[key] = value[field]
                break
    return out


def parse_otlp_json(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Best-effort OTLP/HTTP JSON trace parser. Supports standard resourceSpans/scopeSpans/spans shape."""
    result: list[dict[str, Any]] = []
    for resource_span in payload.get("resourceSpans", []):
        resource_attrs = _attrs(resource_span.get("resource", {}).get("attributes"))
        for scope_span in resource_span.get("scopeSpans", []):
            for span in scope_span.get("spans", []):
                attrs = _attrs(span.get("attributes"))
                merged = {**resource_attrs, **attrs}
                start = int(span.get("startTimeUnixNano") or 0)
                end = int(span.get("endTimeUnixNano") or start)
                latency_ms = max(0.0, (end - start) / 1_000_000)
                status_code = (span.get("status") or {}).get("code")
                error = None
                for event in span.get("events", []):
                    if event.get("name") == "exception":
                        evattrs = _attrs(event.get("attributes"))
                        error = evattrs.get("exception.message") or evattrs.get("exception.type")
                result.append({
                    "trace_id": span.get("traceId") or "otel-unknown",
                    "span_id": span.get("spanId") or f"otel-{len(result)}",
                    "parent_span_id": span.get("parentSpanId") or None,
                    "ts": start / 1_000_000_000 if start else time.time(),
                    "name": span.get("name") or "otel-span",
                    "kind": "otel",
                    "model": merged.get("gen_ai.request.model") or merged.get("llm.model_name"),
                    "input": str(merged.get("gen_ai.prompt") or merged.get("gen_ai.input.messages") or "") or None,
                    "output": str(merged.get("gen_ai.completion") or merged.get("gen_ai.output.messages") or "") or None,
                    "latency_ms": latency_ms,
                    "input_tokens": int(merged.get("gen_ai.usage.input_tokens") or merged.get("llm.token_count.prompt") or 0),
                    "output_tokens": int(merged.get("gen_ai.usage.output_tokens") or merged.get("llm.token_count.completion") or 0),
                    "cost_usd": float(merged.get("aiops.cost_usd") or 0),
                    "status": "error" if status_code in (2, "STATUS_CODE_ERROR") or error else "ok",
                    "error": error,
                    "metadata": merged,
                })
    return result
