from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from logprivacy import CleanerPolicy, clean

from vestigium.config import Config
from vestigium.snapshots.models import JsonValue

_POLICY = CleanerPolicy.default()
_REDACTION_FAILURE = "<redaction unavailable>"
_RECURSION_MARKER = "<recursion detected>"
_MAX_DEPTH_MARKER = "<max depth reached>"
_REPR_UNAVAILABLE = "<repr unavailable>"


@dataclass(frozen=True, slots=True)
class SanitizedValue:
    value: JsonValue
    limitations: list[str]


def sanitize_value(value: Any, config: Config) -> SanitizedValue:
    """Return a bounded, JSON-compatible, LogPrivacy-cleaned value."""

    limitations: list[str] = []
    normalized = _normalize_value(
        value,
        config=config,
        depth=0,
        seen=set(),
        limitations=limitations,
    )
    cleaned = _clean_value(normalized, limitations)
    return SanitizedValue(cleaned, _dedupe(limitations))


def sanitize_mapping(values: Mapping[str, Any], config: Config) -> SanitizedValue:
    """Sanitize mapping values while preserving a JSON object shape."""

    sanitized = sanitize_value(values, config)
    if isinstance(sanitized.value, dict):
        return sanitized

    return SanitizedValue({"value": sanitized.value}, sanitized.limitations)


def sanitize_text(value: str, config: Config) -> SanitizedValue:
    """Sanitize a string with LogPrivacy and configured length limits."""

    limitations: list[str] = []
    truncated = _truncate(value, config, limitations)
    cleaned = _clean_value(truncated, limitations)
    return SanitizedValue(cleaned, _dedupe(limitations))


def safe_repr(value: Any, config: Config) -> SanitizedValue:
    """Render an object defensively, then sanitize the rendered text."""

    try:
        rendered = repr(value)
    except Exception:
        rendered = f"<{type(value).__name__}: {_REPR_UNAVAILABLE}>"
        return SanitizedValue(rendered, ["repr_unavailable"])

    return sanitize_text(rendered, config)


def _normalize_value(
    value: Any,
    *,
    config: Config,
    depth: int,
    seen: set[int],
    limitations: list[str],
) -> JsonValue:
    if depth > config.max_structure_depth:
        limitations.append("max_structure_depth_reached")
        return _MAX_DEPTH_MARKER

    if value is None or isinstance(value, bool | int | float):
        return value

    if isinstance(value, str):
        return _truncate(value, config, limitations)

    if isinstance(value, bytes):
        return _truncate(repr(value), config, limitations)

    value_id = id(value)
    if value_id in seen:
        limitations.append("recursive_value_replaced")
        return _RECURSION_MARKER

    if isinstance(value, Mapping):
        seen.add(value_id)
        return _normalize_mapping(
            value,
            config=config,
            depth=depth,
            seen=seen,
            limitations=limitations,
        )

    if isinstance(value, Sequence):
        seen.add(value_id)
        return _normalize_sequence(
            value,
            config=config,
            depth=depth,
            seen=seen,
            limitations=limitations,
        )

    try:
        rendered = repr(value)
    except Exception:
        limitations.append("repr_unavailable")
        rendered = f"<{type(value).__name__}: {_REPR_UNAVAILABLE}>"

    return _truncate(rendered, config, limitations)


def _normalize_mapping(
    value: Mapping[Any, Any],
    *,
    config: Config,
    depth: int,
    seen: set[int],
    limitations: list[str],
) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= config.max_collection_items:
            limitations.append("collection_items_truncated")
            break

        key_text = _truncate(str(key), config, limitations)
        result[key_text] = _normalize_value(
            item,
            config=config,
            depth=depth + 1,
            seen=seen,
            limitations=limitations,
        )

    seen.discard(id(value))
    return result


def _normalize_sequence(
    value: Sequence[Any],
    *,
    config: Config,
    depth: int,
    seen: set[int],
    limitations: list[str],
) -> list[JsonValue]:
    result: list[JsonValue] = []
    for index, item in enumerate(value):
        if index >= config.max_collection_items:
            limitations.append("collection_items_truncated")
            break

        result.append(
            _normalize_value(
                item,
                config=config,
                depth=depth + 1,
                seen=seen,
                limitations=limitations,
            )
        )

    seen.discard(id(value))
    return result


def _clean_value(value: JsonValue, limitations: list[str]) -> JsonValue:
    try:
        cleaned = clean(value, policy=_POLICY)
    except Exception:
        limitations.append("privacy_sanitizer_failed")
        return _REDACTION_FAILURE

    return _ensure_json_value(cleaned)


def _ensure_json_value(value: Any) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value

    if isinstance(value, Mapping):
        return {str(key): _ensure_json_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_ensure_json_value(item) for item in value]

    if isinstance(value, tuple):
        return [_ensure_json_value(item) for item in value]

    return str(value)


def _truncate(value: str, config: Config, limitations: list[str]) -> str:
    if len(value) <= config.max_value_length:
        return value

    limitations.append("value_truncated")
    return f"{value[: config.max_value_length]}...<truncated>"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
