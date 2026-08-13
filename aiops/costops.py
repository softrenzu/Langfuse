from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from .db import connect, rows_to_dict
from .recording import load_spans

def set_budget(name: str, limit_usd: float, period: str = "month") -> None:
    with connect() as con:
        con.execute("INSERT INTO budgets(name,period,limit_usd,enabled) VALUES(?,?,?,1) ON CONFLICT(name) DO UPDATE SET period=excluded.period,limit_usd=excluded.limit_usd,enabled=1", (name,period,limit_usd))

def budget_status() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    day_start = datetime(now.year,now.month,now.day,tzinfo=timezone.utc).timestamp()
    month_start = datetime(now.year,now.month,1,tzinfo=timezone.utc).timestamp()
    with connect() as con: rules = rows_to_dict(con.execute("SELECT * FROM budgets WHERE enabled=1").fetchall())
    items, out = load_spans(month_start), []
    for rule in rules:
        since = day_start if rule["period"] == "day" else month_start
        spent = sum(s["cost_usd"] for s in items if s["ts"] >= since)
        out.append({**rule,"spent_usd":round(spent,6),"remaining_usd":round(rule["limit_usd"]-spent,6),"breached":spent>rule["limit_usd"]})
    return out
