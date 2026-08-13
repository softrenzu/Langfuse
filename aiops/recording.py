from __future__ import annotations
import json, os, time, uuid
from typing import Any
from .db import connect, rows_to_dict
from .security import redact

def record_span(*, name: str, trace_id: str | None = None, span_id: str | None = None,
                parent_span_id: str | None = None, model: str | None = None, input: Any = None,
                output: Any = None, latency_ms: float = 0, input_tokens: int = 0,
                output_tokens: int = 0, cost_usd: float = 0, status: str = "ok",
                error: str | None = None, metadata: dict[str, Any] | None = None,
                ts: float | None = None) -> dict[str, str]:
    p = {"trace_id": trace_id or uuid.uuid4().hex, "span_id": span_id or uuid.uuid4().hex[:16],
         "parent_span_id": parent_span_id, "ts": ts or time.time(), "name": name, "kind": "llm",
         "model": model, "input": input, "output": output, "latency_ms": latency_ms,
         "input_tokens": input_tokens, "output_tokens": output_tokens, "cost_usd": cost_usd,
         "status": status, "error": error, "metadata": metadata or {}}
    if os.getenv("AIOPS_REDACT", "1") != "0":
        for key in ("input", "output", "error", "metadata"): p[key] = redact(p[key])
    text = lambda v: v if v is None or isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    with connect() as con:
        con.execute("INSERT INTO spans(trace_id,span_id,parent_span_id,ts,name,kind,model,input,output,latency_ms,input_tokens,output_tokens,cost_usd,status,error,metadata) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (p["trace_id"],p["span_id"],p["parent_span_id"],p["ts"],p["name"],p["kind"],p["model"],text(p["input"]),text(p["output"]),p["latency_ms"],p["input_tokens"],p["output_tokens"],p["cost_usd"],p["status"],p["error"],json.dumps(p["metadata"],ensure_ascii=False)))
    return {"trace_id": p["trace_id"], "span_id": p["span_id"]}

def load_spans(since: float | None = None, limit: int = 10000) -> list[dict[str, Any]]:
    sql, args = "SELECT * FROM spans", []
    if since is not None: sql += " WHERE ts >= ?"; args.append(since)
    sql += " ORDER BY ts DESC LIMIT ?"; args.append(limit)
    with connect() as con: return rows_to_dict(con.execute(sql, args).fetchall())
