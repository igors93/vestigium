from __future__ import annotations

import inspect
import linecache
from collections.abc import Callable
from contextlib import AbstractContextManager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, Literal, cast

from vestigium.config import Config
from vestigium.privacy.adapter import sanitize_mapping, sanitize_text
from vestigium.snapshots.models import EventSnapshot, JsonValue, SourceLocation


@dataclass(frozen=True, slots=True)
class ContextFrame:
    name: str
    data: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class RuntimeState:
    contexts: tuple[ContextFrame, ...] = ()
    events: tuple[EventSnapshot, ...] = ()
    next_sequence: int = 1
    limitations: tuple[str, ...] = ()

    @property
    def operation(self) -> str | None:
        if not self.contexts:
            return None
        return self.contexts[-1].name


_STATE: ContextVar[RuntimeState | None] = ContextVar(
    "vestigium_runtime_state",
    default=None,
)


class OperationContext(AbstractContextManager["OperationContext"]):
    """Logical operation scope tracked only in memory until an incident occurs."""

    def __init__(
        self,
        name: str,
        data: dict[str, Any],
        *,
        config_getter: Callable[[], Config],
        exception_capture: Callable[[BaseException, int], object],
    ) -> None:
        self._name = name
        self._data = data
        self._config_getter = config_getter
        self._exception_capture = exception_capture
        self._previous_state: RuntimeState | None = None
        self._previous_depth = 0

    def __enter__(self) -> OperationContext:
        config = self._config_getter()
        state = get_state()
        sanitized = sanitize_mapping(self._data, config)
        name = _sanitize_name(self._name, config)
        frame = ContextFrame(
            name=name,
            data=cast(dict[str, JsonValue], sanitized.value),
        )
        self._previous_state = state
        self._previous_depth = len(state.contexts)
        set_state(
            RuntimeState(
                contexts=(*state.contexts, frame),
                events=state.events,
                next_sequence=state.next_sequence,
                limitations=_merge_limitations(
                    state.limitations,
                    tuple(sanitized.limitations),
                ),
            )
        )
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback_object: TracebackType | None,
    ) -> Literal[False]:
        if exception is not None:
            self._exception_capture(exception, 3)

        previous_state = self._previous_state or RuntimeState()
        current = get_state()
        if self._previous_depth == 0:
            set_state(previous_state)
            return False

        set_state(
            RuntimeState(
                contexts=current.contexts[: self._previous_depth],
                events=current.events,
                next_sequence=current.next_sequence,
                limitations=current.limitations,
            )
        )
        return False


def get_state() -> RuntimeState:
    return _STATE.get() or RuntimeState()


def set_state(state: RuntimeState) -> None:
    _STATE.set(state)


def reset_state() -> None:
    _STATE.set(RuntimeState())


def record_event(name: str, data: dict[str, Any], config: Config, *, skip: int) -> None:
    state = get_state()
    sanitized = sanitize_mapping(data, config)
    event_name = _sanitize_name(name, config)
    event = EventSnapshot(
        sequence=state.next_sequence,
        name=event_name,
        recorded_at=_utc_now(),
        data=cast(dict[str, JsonValue], sanitized.value),
        context=[frame.name for frame in state.contexts],
        source=capture_source(skip),
    )
    events = (*state.events, event)
    limitations = _merge_limitations(
        state.limitations,
        tuple(sanitized.limitations),
    )

    if config.event_limit == 0:
        events = ()
        limitations = _merge_limitations(limitations, ("event_buffer_disabled",))
    elif len(events) > config.event_limit:
        events = events[-config.event_limit :]
        limitations = _merge_limitations(limitations, ("event_buffer_truncated",))

    set_state(
        RuntimeState(
            contexts=state.contexts,
            events=events,
            next_sequence=state.next_sequence + 1,
            limitations=limitations,
        )
    )


def capture_source(skip: int = 1) -> SourceLocation | None:
    frame = inspect.currentframe()
    try:
        for _ in range(skip):
            if frame is None:
                return None
            frame = frame.f_back

        if frame is None:
            return None

        filename = frame.f_code.co_filename
        line_number = frame.f_lineno
        source = linecache.getline(filename, line_number).strip() or None
        return SourceLocation(
            file=filename,
            line=line_number,
            function=frame.f_code.co_name,
            source=source,
        )
    finally:
        del frame


def _sanitize_name(name: str, config: Config) -> str:
    sanitized = sanitize_text(name, config)
    return str(sanitized.value)


def _merge_limitations(
    existing: tuple[str, ...],
    new: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*existing, *new)))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
