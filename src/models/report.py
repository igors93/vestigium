from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FrameInfo:
    file: str
    line: int | None
    function: str
    source: str | None


@dataclass(frozen=True, slots=True)
class ErrorReport:
    error_id: str
    project_name: str
    captured_at: str
    exception_type: str
    exception_message: str
    frames: list[FrameInfo]
    local_variables: dict[str, str]
    environment: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
