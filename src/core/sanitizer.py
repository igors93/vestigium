from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_TERMS = {
    "authorization",
    "card",
    "cookie",
    "credential",
    "key",
    "passwd",
    "password",
    "secret",
    "token",
}

SENSITIVE_COMPACT_NAMES = {
    "apikey",
    "cardnumber",
}


def sanitize_mapping(
    values: Mapping[str, Any],
    max_length: int = 500,
) -> dict[str, str]:
    """Convert values to safe text and redact sensitive names."""

    return {
        name: (
            "<redacted>" if _is_sensitive_name(name) else safe_repr(value, max_length)
        )
        for name, value in values.items()
    }


def safe_repr(value: Any, max_length: int = 500) -> str:
    """Return a defensive and size-limited representation."""

    if max_length < 0:
        raise ValueError("max_length must be zero or greater")

    try:
        rendered = repr(value)
    except Exception:
        rendered = f"<{type(value).__name__}: unavailable>"

    if len(rendered) <= max_length:
        return rendered

    return f"{rendered[:max_length]}...<truncated>"


def _is_sensitive_name(name: str) -> bool:
    normalized_name = _normalize_identifier(name)

    if normalized_name in SENSITIVE_COMPACT_NAMES:
        return True

    parts = {part for part in normalized_name.split("_") if part}
    return bool(parts.intersection(SENSITIVE_TERMS))


def _normalize_identifier(name: str) -> str:
    with_word_boundaries = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return re.sub(r"[^a-zA-Z0-9]+", "_", with_word_boundaries).lower()
