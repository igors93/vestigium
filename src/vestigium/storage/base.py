from __future__ import annotations

from pathlib import Path
from typing import Protocol

from vestigium.snapshots.models import Snapshot


class SnapshotStore(Protocol):
    """Persistence boundary for forensic snapshots."""

    def save(self, snapshot: Snapshot) -> str | Path | None:
        """Persist a snapshot and return its location when available."""
