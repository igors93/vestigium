from __future__ import annotations

from pathlib import Path
from threading import Lock

import pytest

from vestigium import configure, stop
from vestigium.runtime import reset_state
from vestigium.snapshots.models import Snapshot


class MemoryStore:
    def __init__(self) -> None:
        self.snapshots: list[Snapshot] = []
        self._lock = Lock()

    def save(self, snapshot: Snapshot) -> Path | None:
        with self._lock:
            self.snapshots.append(snapshot)
        return None


class FailingStore:
    def save(self, snapshot: Snapshot) -> Path | None:
        raise OSError("disk unavailable")


@pytest.fixture(autouse=True)
def clean_vestigium(tmp_path):
    stop()
    reset_state()
    configure(
        project_name="test-project",
        snapshot_directory=str(tmp_path / "snapshots"),
        capture_uncaught_exceptions=False,
    )

    yield

    stop()
    reset_state()


@pytest.fixture
def memory_store() -> MemoryStore:
    return MemoryStore()
