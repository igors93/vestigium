from __future__ import annotations

import os
import platform
import sys
import threading
import traceback
from datetime import datetime, timezone
from types import TracebackType
from typing import cast

from vestigium.config import Config
from vestigium.incidents.models import IncidentInput
from vestigium.privacy.adapter import sanitize_mapping, sanitize_text, sanitize_value
from vestigium.runtime import RuntimeState
from vestigium.snapshots.models import (
    ContextSnapshot,
    EventSnapshot,
    ExceptionInfo,
    Incident,
    JsonValue,
    Snapshot,
    SourceLocation,
    StackFrame,
)
from vestigium.utils.identifiers import create_incident_id

SCHEMA_VERSION = "1.0"


def build_snapshot(
    incident_input: IncidentInput,
    *,
    config: Config,
    state: RuntimeState,
    exception: BaseException | None = None,
    traceback_object: TracebackType | None = None,
) -> Snapshot:
    """Build a versioned forensic snapshot from observed execution facts."""

    limitations = list(state.limitations)
    captured_at = datetime.now(timezone.utc).isoformat()
    operation = state.operation
    incident = _build_incident(
        incident_input,
        config=config,
        captured_at=captured_at,
        operation=operation,
        limitations=limitations,
    )
    exception_info = _build_exception_info(
        exception,
        traceback_object,
        config=config,
        limitations=limitations,
    )
    events = [
        _sanitize_event(event, config=config, limitations=limitations)
        for event in state.events
    ]
    context = ContextSnapshot(
        active=[
            {
                "name": frame.name,
                "data": frame.data,
            }
            for frame in state.contexts
        ],
        operation=operation,
    )

    return Snapshot(
        schema_version=SCHEMA_VERSION,
        incident=incident,
        exception=exception_info,
        execution=_build_execution(incident_input, operation),
        context=context,
        events=events,
        reproduction=_build_reproduction(incident, events, config, limitations),
        environment=_build_environment(config, limitations),
        application=_build_application(config, limitations),
        limitations=_dedupe(limitations),
        privacy={
            "sanitized": True,
            "engine": "logprivacy",
            "policy": "default",
        },
    )


def _build_incident(
    incident_input: IncidentInput,
    *,
    config: Config,
    captured_at: str,
    operation: str | None,
    limitations: list[str],
) -> Incident:
    expected = sanitize_value(incident_input.expected, config)
    actual = sanitize_value(incident_input.actual, config)
    metadata = sanitize_mapping(incident_input.metadata, config)
    name = _clean_str(incident_input.name, config, limitations)
    message = (
        _clean_str(incident_input.message, config, limitations)
        if incident_input.message is not None
        else None
    )
    severity = _clean_str(incident_input.severity, config, limitations)
    source = _clean_str(incident_input.source, config, limitations)

    limitations.extend(expected.limitations)
    limitations.extend(actual.limitations)
    limitations.extend(metadata.limitations)

    return Incident(
        id=create_incident_id(),
        type=incident_input.type,
        name=name,
        message=message,
        severity=severity,
        captured_at=captured_at,
        source=source,
        operation=operation,
        expected=expected.value,
        actual=actual.value,
        tags=[_clean_str(tag, config, limitations) for tag in incident_input.tags],
        metadata=cast(dict[str, JsonValue], metadata.value),
        origin=_sanitize_source(incident_input.origin, config, limitations),
    )


def _build_exception_info(
    exception: BaseException | None,
    traceback_object: TracebackType | None,
    *,
    config: Config,
    limitations: list[str],
) -> ExceptionInfo | None:
    if exception is None:
        return None

    return ExceptionInfo(
        type=type(exception).__name__,
        module=type(exception).__module__,
        message=_exception_message(exception, config, limitations),
        traceback=_extract_traceback(
            traceback_object,
            config=config,
            limitations=limitations,
        ),
        chain=_extract_exception_chain(exception, config, limitations),
    )


def _extract_traceback(
    traceback_object: TracebackType | None,
    *,
    config: Config,
    limitations: list[str],
) -> list[StackFrame]:
    if traceback_object is None:
        return []

    summaries = list(traceback.extract_tb(traceback_object))
    if len(summaries) > config.max_frames:
        limitations.append("traceback_frames_truncated")
        summaries = summaries[-config.max_frames :] if config.max_frames > 0 else []

    local_variables = _extract_failing_locals(
        traceback_object,
        config=config,
        limitations=limitations,
    )
    frames: list[StackFrame] = []
    for index, frame in enumerate(summaries):
        is_failing_frame = index == len(summaries) - 1
        frames.append(
            StackFrame(
                file=_clean_str(frame.filename, config, limitations),
                line=frame.lineno,
                function=_clean_str(frame.name, config, limitations),
                source=(
                    _clean_str(frame.line, config, limitations)
                    if frame.line is not None
                    else None
                ),
                locals=local_variables if is_failing_frame else {},
            )
        )
    return frames


def _extract_failing_locals(
    traceback_object: TracebackType,
    *,
    config: Config,
    limitations: list[str],
) -> dict[str, JsonValue]:
    if not config.capture_locals:
        return {}

    last_traceback = traceback_object
    while last_traceback.tb_next is not None:
        last_traceback = last_traceback.tb_next

    sanitized = sanitize_mapping(last_traceback.tb_frame.f_locals, config)
    limitations.extend(sanitized.limitations)
    return cast(dict[str, JsonValue], sanitized.value)


def _extract_exception_chain(
    exception: BaseException,
    config: Config,
    limitations: list[str],
) -> list[dict[str, str]]:
    chain: list[dict[str, str]] = []
    seen: set[int] = set()
    current = exception.__cause__ or exception.__context__

    while current is not None and id(current) not in seen and len(chain) < 5:
        seen.add(id(current))
        chain.append(
            {
                "type": type(current).__name__,
                "module": type(current).__module__,
                "message": _exception_message(current, config, limitations),
            }
        )
        current = current.__cause__ or current.__context__

    if current is not None:
        limitations.append("exception_chain_truncated")

    return chain


def _exception_message(
    exception: BaseException,
    config: Config,
    limitations: list[str],
) -> str:
    try:
        message = str(exception)
    except Exception:
        limitations.append("exception_message_unavailable")
        return f"<{type(exception).__name__}: message unavailable>"

    return _clean_str(message, config, limitations)


def _sanitize_event(
    event: EventSnapshot,
    *,
    config: Config,
    limitations: list[str],
) -> EventSnapshot:
    return EventSnapshot(
        sequence=event.sequence,
        name=_clean_str(event.name, config, limitations),
        recorded_at=event.recorded_at,
        data=event.data,
        context=[_clean_str(name, config, limitations) for name in event.context],
        source=_sanitize_source(event.source, config, limitations),
    )


def _sanitize_source(
    source: SourceLocation | None,
    config: Config,
    limitations: list[str],
) -> SourceLocation | None:
    if source is None:
        return None

    return SourceLocation(
        file=_clean_str(source.file, config, limitations),
        line=source.line,
        function=_clean_str(source.function, config, limitations),
        source=(
            _clean_str(source.source, config, limitations)
            if source.source is not None
            else None
        ),
    )


def _build_execution(
    incident_input: IncidentInput,
    operation: str | None,
) -> dict[str, JsonValue]:
    return {
        "trigger": incident_input.type,
        "source": incident_input.source,
        "operation": operation,
        "process_id": os.getpid(),
        "thread_id": threading.get_ident(),
        "thread_name": threading.current_thread().name,
    }


def _build_reproduction(
    incident: Incident,
    events: list[EventSnapshot],
    config: Config,
    limitations: list[str],
) -> dict[str, JsonValue]:
    data = sanitize_value(
        {
            "operation": incident.operation,
            "expected": incident.expected,
            "actual": incident.actual,
            "event_names": [event.name for event in events],
            "application_version": config.application_version,
        },
        config,
    )
    limitations.extend(data.limitations)
    if not events:
        limitations.append("no_events_recorded")
    return data.value if isinstance(data.value, dict) else {}


def _build_environment(
    config: Config,
    limitations: list[str],
) -> dict[str, JsonValue]:
    data = sanitize_value(
        {
            "python_version": sys.version.split()[0],
            "operating_system": platform.platform(),
            "working_directory": os.getcwd(),
            "timezone": datetime.now().astimezone().tzname(),
        },
        config,
    )
    limitations.extend(data.limitations)
    return data.value if isinstance(data.value, dict) else {}


def _build_application(
    config: Config,
    limitations: list[str],
) -> dict[str, JsonValue]:
    data = sanitize_value(
        {
            "project_name": config.project_name,
            "version": config.application_version,
        },
        config,
    )
    limitations.extend(data.limitations)
    return data.value if isinstance(data.value, dict) else {}


def _clean_str(value: str, config: Config, limitations: list[str]) -> str:
    sanitized = sanitize_text(value, config)
    limitations.extend(sanitized.limitations)
    return str(sanitized.value)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
