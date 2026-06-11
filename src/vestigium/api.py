from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from functools import wraps
from types import TracebackType
from typing import Any, ParamSpec, TypeVar

from .config import Config
from .incidents.models import IncidentInput
from .runtime import OperationContext, capture_source, get_state, record_event
from .snapshots.builder import build_snapshot
from .snapshots.models import IncidentType, Snapshot
from .storage.base import SnapshotStore
from .storage.json_store import JsonSnapshotStore

P = ParamSpec("P")
R = TypeVar("R")

_CONFIG = Config()
_CAPTURED_MARKER = "__vestigium_snapshot_captured__"


class InvariantViolation(AssertionError):
    """Raised only when invariant(..., raise_on_failure=True) is requested."""


def configure(
    project_name: str = "python-project",
    snapshot_directory: str = ".vestigium",
    application_version: str | None = None,
    capture_locals: bool = True,
    capture_uncaught_exceptions: bool = True,
    event_limit: int = 50,
    max_value_length: int = 500,
    max_structure_depth: int = 4,
    max_collection_items: int = 25,
    max_frames: int = 25,
    store: SnapshotStore | None = None,
) -> Config:
    """Configure Vestigium for forensic snapshot capture."""

    from vestigium.integrations.excepthook import install_excepthook

    global _CONFIG

    config = Config(
        project_name=project_name,
        snapshot_directory=snapshot_directory,
        application_version=application_version,
        capture_locals=capture_locals,
        capture_uncaught_exceptions=capture_uncaught_exceptions,
        event_limit=event_limit,
        max_value_length=max_value_length,
        max_structure_depth=max_structure_depth,
        max_collection_items=max_collection_items,
        max_frames=max_frames,
        store=store,
    )
    _CONFIG = config

    if capture_uncaught_exceptions:
        install_excepthook(config)

    return config


def context(name: str, **data: Any) -> OperationContext:
    """Track a logical operation in memory until an incident occurs."""

    return OperationContext(
        name,
        data,
        config_getter=get_config,
        exception_capture=lambda error, skip: capture_exception(
            error,
            source="context_manager",
            origin_skip=skip,
        ),
    )


def event(name: str, **data: Any) -> None:
    """Record a bounded in-memory breadcrumb for the current execution."""

    try:
        record_event(name, data, get_config(), skip=3)
    except Exception:
        pass


def anomaly(
    name: str,
    *,
    expected: Any = None,
    actual: Any = None,
    message: str | None = None,
    severity: str = "warning",
    tags: Sequence[str] = (),
    metadata: dict[str, Any] | None = None,
) -> Snapshot | None:
    """Capture an explicit anomalous behavior as a forensic snapshot."""

    return _capture_incident(
        incident_type="anomaly",
        name=name,
        message=message,
        severity=severity,
        source="explicit",
        expected=expected,
        actual=actual,
        tags=tags,
        metadata=metadata,
        origin_skip=3,
    )


def invariant(
    condition: bool,
    name: str,
    *,
    expected: Any = None,
    actual: Any = None,
    message: str | None = None,
    severity: str = "error",
    tags: Sequence[str] = (),
    metadata: dict[str, Any] | None = None,
    raise_on_failure: bool = False,
) -> Snapshot | None:
    """Capture an invariant violation when condition is false.

    By default this records evidence and lets the application continue.
    Set raise_on_failure=True when the caller wants an AssertionError after capture.
    """

    if condition:
        return None

    snapshot = _capture_incident(
        incident_type="invariant_violation",
        name=name,
        message=message,
        severity=severity,
        source="explicit",
        expected=expected,
        actual=actual,
        tags=tags,
        metadata=metadata,
        origin_skip=3,
    )

    if raise_on_failure:
        raise InvariantViolation(name)

    return snapshot


def unexpected_result(
    name: str,
    *,
    expected: Any = None,
    actual: Any = None,
    message: str | None = None,
    severity: str = "warning",
    tags: Sequence[str] = (),
    metadata: dict[str, Any] | None = None,
) -> Snapshot | None:
    """Capture a result that violates caller-defined expectations."""

    return _capture_incident(
        incident_type="unexpected_result",
        name=name,
        message=message,
        severity=severity,
        source="explicit",
        expected=expected,
        actual=actual,
        tags=tags,
        metadata=metadata,
        origin_skip=3,
    )


def capture(
    name: str = "manual_capture",
    *,
    message: str | None = None,
    severity: str = "info",
    expected: Any = None,
    actual: Any = None,
    tags: Sequence[str] = (),
    metadata: dict[str, Any] | None = None,
) -> Snapshot | None:
    """Persist a manual forensic snapshot without implying a root cause."""

    return _capture_incident(
        incident_type="manual_capture",
        name=name,
        message=message,
        severity=severity,
        source="explicit",
        expected=expected,
        actual=actual,
        tags=tags,
        metadata=metadata,
        origin_skip=3,
    )


def capture_exception(
    exception: BaseException,
    *,
    name: str | None = None,
    severity: str = "error",
    source: str = "explicit",
    metadata: dict[str, Any] | None = None,
    origin_skip: int = 3,
) -> Snapshot | None:
    """Capture a snapshot for an exception without swallowing it."""

    if getattr(exception, _CAPTURED_MARKER, False):
        return None

    snapshot = _capture_incident(
        incident_type="exception",
        name=name or type(exception).__name__,
        message=None,
        severity=severity,
        source=source,
        expected=None,
        actual=None,
        tags=(),
        metadata=metadata,
        exception=exception,
        traceback_object=exception.__traceback__,
        origin_skip=origin_skip,
    )
    _mark_exception_captured(exception)
    return snapshot


def trace(
    name: str | None = None, **context_data: Any
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator convenience around context()."""

    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        operation_name = name or function.__qualname__

        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with context(operation_name, **context_data):
                return function(*args, **kwargs)

        return wrapper

    return decorator


def get_config() -> Config:
    """Return the active runtime configuration."""

    return _CONFIG


def shutdown() -> None:
    """Uninstall automatic exception capture."""

    from vestigium.integrations.excepthook import uninstall_excepthook

    uninstall_excepthook()


def stop() -> None:
    """Compatibility alias for shutdown()."""

    shutdown()


def start(
    project_name: str = "python-project",
    reports_directory: str = ".vestigium",
    capture_locals: bool = True,
) -> Config:
    """Compatibility wrapper for configure()."""

    return configure(
        project_name=project_name,
        snapshot_directory=reports_directory,
        capture_locals=capture_locals,
    )


def _capture_incident(
    *,
    incident_type: IncidentType,
    name: str,
    message: str | None,
    severity: str,
    source: str,
    expected: Any,
    actual: Any,
    tags: Sequence[str],
    metadata: dict[str, Any] | None,
    origin_skip: int,
    exception: BaseException | None = None,
    traceback_object: TracebackType | None = None,
) -> Snapshot | None:
    try:
        config = get_config()
        incident = IncidentInput(
            type=incident_type,
            name=name,
            message=message,
            severity=severity,
            source=source,
            expected=expected,
            actual=actual,
            tags=tuple(tags),
            metadata=metadata or {},
            origin=capture_source(origin_skip),
        )
        snapshot = build_snapshot(
            incident,
            config=config,
            state=get_state(),
            exception=exception,
            traceback_object=traceback_object,
        )
        _persist_snapshot(snapshot, config)
        return snapshot
    except Exception as error:
        print(f"[Vestigium] Snapshot capture failed: {error}", file=sys.stderr)
        return None


def _persist_snapshot(snapshot: Snapshot, config: Config) -> None:
    store = config.store or JsonSnapshotStore(config.snapshot_path)
    try:
        store.save(snapshot)
    except Exception as error:
        print(f"[Vestigium] Snapshot persistence failed: {error}", file=sys.stderr)


def _mark_exception_captured(exception: BaseException) -> None:
    try:
        setattr(exception, _CAPTURED_MARKER, True)
    except Exception:
        return
