from __future__ import annotations

from typing import Any, Mapping


SENSITIVE_TERMS = {
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "card_number",
}


def sanitize_mapping(
    values: Mapping[str, Any],
    max_length: int = 500,
) -> dict[str, str]:
    """Convert values to safe text and redact sensitive names."""

    result: dict[str, str] = {}

    for name, value in values.items():
        result[name] = (
            "<redacted>"
            if _is_sensitive_name(name)
            else safe_repr(value, max_length)
        )

    return result


def safe_repr(value: Any, max_length: int = 500) -> str:
    """Return a defensive and size-limited representation."""

    try:
        rendered = repr(value)
    except Exception:
        rendered = f"<{type(value).__name__}: unavailable>"

    if len(rendered) <= max_length:
        return rendered

    return f"{rendered[:max_length]}...<truncated>"


def _is_sensitive_name(name: str) -> bool:
    normalized_name = name.lower()
    return any(term in normalized_name for term in SENSITIVE_TERMS)
