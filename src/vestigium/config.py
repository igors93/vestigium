from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vestigium.storage.base import SnapshotStore


@dataclass(frozen=True, slots=True)
class Config:
    """Runtime configuration for forensic snapshot capture."""

    project_name: str = "python-project"
    snapshot_directory: str = ".vestigium"
    application_version: str | None = None
    capture_locals: bool = True
    capture_uncaught_exceptions: bool = True
    event_limit: int = 50
    max_value_length: int = 500
    max_structure_depth: int = 4
    max_collection_items: int = 25
    max_frames: int = 25
    store: SnapshotStore | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        _require_non_negative("event_limit", self.event_limit)
        _require_non_negative("max_value_length", self.max_value_length)
        _require_non_negative("max_structure_depth", self.max_structure_depth)
        _require_non_negative("max_collection_items", self.max_collection_items)
        _require_non_negative("max_frames", self.max_frames)

    @property
    def snapshot_path(self) -> Path:
        return Path(self.snapshot_directory)


def _require_non_negative(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be zero or greater")
