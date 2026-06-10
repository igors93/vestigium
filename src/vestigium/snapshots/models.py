from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, TypeAlias

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)

IncidentType = Literal[
    "exception",
    "anomaly",
    "invariant_violation",
    "unexpected_result",
    "manual_capture",
]


@dataclass(frozen=True, slots=True)
class SourceLocation:
    file: str
    line: int | None
    function: str
    source: str | None


@dataclass(frozen=True, slots=True)
class Incident:
    id: str
    type: IncidentType
    name: str
    message: str | None
    severity: str
    captured_at: str
    source: str
    operation: str | None
    expected: JsonValue
    actual: JsonValue
    tags: list[str]
    metadata: dict[str, JsonValue]
    origin: SourceLocation | None


@dataclass(frozen=True, slots=True)
class StackFrame:
    file: str
    line: int | None
    function: str
    source: str | None
    locals: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class ExceptionInfo:
    type: str
    module: str
    message: str
    traceback: list[StackFrame]
    chain: list[dict[str, str]]


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    active: list[dict[str, JsonValue]]
    operation: str | None


@dataclass(frozen=True, slots=True)
class EventSnapshot:
    sequence: int
    name: str
    recorded_at: str
    data: dict[str, JsonValue]
    context: list[str]
    source: SourceLocation | None


@dataclass(frozen=True, slots=True)
class Snapshot:
    schema_version: str
    incident: Incident
    exception: ExceptionInfo | None
    execution: dict[str, JsonValue]
    context: ContextSnapshot
    events: list[EventSnapshot]
    reproduction: dict[str, JsonValue]
    environment: dict[str, JsonValue]
    application: dict[str, JsonValue]
    limitations: list[str]
    privacy: dict[str, JsonValue]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
