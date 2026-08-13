from __future__ import annotations

import re
from typing import Any

_PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)(?:\+?81[- ]?)?0\d{1,4}[- ]?\d{1,4}[- ]?\d{3,4}(?!\d)"), "[REDACTED_PHONE]"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_CARD]"),
    (re.compile(r"(?i)(api[_-]?key|authorization|bearer|secret|password)\s*[:=]\s*[^\s,;]+"), r"\1=[REDACTED_SECRET]"),
]


def redact_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: ("[REDACTED_SECRET]" if k.lower() in {"password", "secret", "api_key", "apikey", "authorization"} else redact(v)) for k, v in value.items()}
    return value


def contains_sensitive(value: str | None) -> bool:
    if not value:
        return False
    return redact_text(value) != value
