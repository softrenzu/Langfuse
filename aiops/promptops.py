from __future__ import annotations
import json, time
from typing import Any
from .db import connect, rows_to_dict

def put_prompt(name: str, content: str, labels: list[str] | None = None) -> int:
    with connect() as con:
        version = con.execute("SELECT COALESCE(MAX(version),0)+1 FROM prompts WHERE name=?", (name,)).fetchone()[0]
        con.execute("INSERT INTO prompts(name,version,content,labels,created_at) VALUES(?,?,?,?,?)", (name,version,content,json.dumps(labels or []),time.time()))
    return version

def get_prompt(name: str, label: str | None = None) -> dict[str, Any] | None:
    with connect() as con: items = rows_to_dict(con.execute("SELECT * FROM prompts WHERE name=? ORDER BY version DESC", (name,)).fetchall())
    if label: items = [x for x in items if label in x["labels"]]
    return items[0] if items else None
