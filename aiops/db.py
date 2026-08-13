from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DEFAULT_DB = os.getenv("AIOPS_DB", "./data/aiops.db")
_lock = threading.RLock()

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS spans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trace_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  parent_span_id TEXT,
  ts REAL NOT NULL,
  name TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'internal',
  model TEXT,
  input TEXT,
  output TEXT,
  latency_ms REAL NOT NULL DEFAULT 0,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ok',
  error TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id, ts);
CREATE INDEX IF NOT EXISTS idx_spans_ts ON spans(ts);
CREATE INDEX IF NOT EXISTS idx_spans_name ON spans(name, model, ts);

CREATE TABLE IF NOT EXISTS prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  version INTEGER NOT NULL,
  content TEXT NOT NULL,
  labels TEXT NOT NULL DEFAULT '[]',
  created_at REAL NOT NULL,
  UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS budgets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  period TEXT NOT NULL,
  limit_usd REAL NOT NULL,
  match_key TEXT,
  match_value TEXT,
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS alert_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  metric TEXT NOT NULL,
  op TEXT NOT NULL,
  threshold REAL NOT NULL,
  window_minutes INTEGER NOT NULL DEFAULT 60,
  enabled INTEGER NOT NULL DEFAULT 1
);
"""


def _path() -> str:
    return os.getenv("AIOPS_DB", DEFAULT_DB)


def init_db() -> None:
    path = _path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        con = sqlite3.connect(path)
        try:
            con.executescript(SCHEMA)
            con.commit()
        finally:
            con.close()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    init_db()
    with _lock:
        con = sqlite3.connect(_path(), timeout=30, check_same_thread=False)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()


def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for key in ("metadata", "labels"):
            if key in item and isinstance(item[key], str):
                try:
                    item[key] = json.loads(item[key])
                except json.JSONDecodeError:
                    pass
        result.append(item)
    return result
