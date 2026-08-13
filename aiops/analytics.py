from __future__ import annotations

import hashlib
import math
import statistics
from collections import Counter, defaultdict
from typing import Any


def safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    idx = min(len(vals) - 1, max(0, math.ceil(q * len(vals)) - 1))
    return float(vals[idx])


def anomaly_score(value: float, history: list[float]) -> float:
    """Robust anomaly score using median absolute deviation."""
    if len(history) < 5:
        return 0.0
    med = statistics.median(history)
    deviations = [abs(x - med) for x in history]
    mad = statistics.median(deviations)
    if mad == 0:
        return 0.0 if value == med else min(20.0, abs(value - med) / max(abs(med), 1.0) * 5.0)
    return abs(0.6745 * (value - med) / mad)


def incident_fingerprint(span: dict[str, Any]) -> str:
    raw = "|".join([
        str(span.get("name") or ""),
        str(span.get("model") or ""),
        str(span.get("status") or ""),
        (str(span.get("error") or "").lower()[:120]),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def recommend_fix(span: dict[str, Any]) -> list[str]:
    error = (span.get("error") or "").lower()
    recs: list[str] = []
    if "rate" in error and "limit" in error:
        recs.append("指数バックオフとジッターを追加し、モデル単位の同時実行数を制限する")
    if "timeout" in error or span.get("latency_ms", 0) > 15_000:
        recs.append("タイムアウトを明示し、低遅延モデルまたはキャッシュへのフォールバックを設定する")
    if "json" in error or "parse" in error:
        recs.append("JSON Schema/structured outputを有効化し、パース失敗時のみ再試行する")
    if span.get("cost_usd", 0) > 0.10:
        recs.append("最大出力トークンを制限し、同品質なら安価なモデルへのルーティングを検討する")
    if span.get("status") == "error" and not recs:
        recs.append("同一fingerprintの直前成功トレースと差分比較し、入力・モデル・ツール変更点を切り分ける")
    return recs


def build_incidents(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_series: dict[tuple[str, str], list[float]] = defaultdict(list)
    for s in spans:
        by_series[(s.get("name") or "", s.get("model") or "")].append(float(s.get("latency_ms") or 0))

    for s in spans:
        hist = by_series[(s.get("name") or "", s.get("model") or "")]
        score = anomaly_score(float(s.get("latency_ms") or 0), hist)
        is_incident = s.get("status") == "error" or score >= 4.0
        if is_incident:
            item = dict(s)
            item["anomaly_score"] = round(score, 2)
            by_key[incident_fingerprint(item)].append(item)

    incidents = []
    for fp, items in by_key.items():
        latest = max(items, key=lambda x: x.get("ts", 0))
        incidents.append({
            "fingerprint": fp,
            "count": len(items),
            "latest_ts": latest.get("ts"),
            "name": latest.get("name"),
            "model": latest.get("model"),
            "status": latest.get("status"),
            "error": latest.get("error"),
            "max_anomaly_score": max(i.get("anomaly_score", 0) for i in items),
            "recommendations": recommend_fix(latest),
            "trace_ids": list(dict.fromkeys(i.get("trace_id") for i in items))[:10],
        })
    return sorted(incidents, key=lambda x: (x["latest_ts"] or 0), reverse=True)


def summarize(spans: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [float(s.get("latency_ms") or 0) for s in spans]
    costs = [float(s.get("cost_usd") or 0) for s in spans]
    errors = [s for s in spans if s.get("status") == "error"]
    models = Counter((s.get("model") or "unknown") for s in spans)
    trace_count = len({s.get("trace_id") for s in spans})
    return {
        "spans": len(spans),
        "traces": trace_count,
        "error_rate": round(len(errors) / len(spans), 4) if spans else 0,
        "latency_ms": {
            "avg": round(safe_mean(latencies), 2),
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
        },
        "cost_usd": round(sum(costs), 6),
        "input_tokens": sum(int(s.get("input_tokens") or 0) for s in spans),
        "output_tokens": sum(int(s.get("output_tokens") or 0) for s in spans),
        "top_models": models.most_common(8),
    }


def compare_variants(spans: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in spans:
        metadata = s.get("metadata") or {}
        value = metadata.get(key)
        if value is not None:
            groups[str(value)].append(s)
    result = []
    for value, items in groups.items():
        summary = summarize(items)
        summary["variant"] = value
        result.append(summary)
    return sorted(result, key=lambda x: x["variant"])
