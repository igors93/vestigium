from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vestigium.snapshots.models import IncidentType, SourceLocation


@dataclass(frozen=True, slots=True)
class IncidentInput:
    type: IncidentType
    name: str
    message: str | None
    severity: str
    source: str
    expected: Any
    actual: Any
    tags: tuple[str, ...]
    metadata: dict[str, Any]
    origin: SourceLocation | None
