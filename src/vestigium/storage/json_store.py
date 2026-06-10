from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from vestigium.snapshots.models import Snapshot


class JsonSnapshotStore:
    """Local JSON snapshot store with atomic writes."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def save(self, snapshot: Snapshot) -> Path:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination = self.directory / f"{snapshot.incident.id}.json"
        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.directory,
                prefix=f".{snapshot.incident.id}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temp_path = Path(temporary.name)
                json.dump(
                    snapshot.to_dict(),
                    temporary,
                    indent=2,
                    ensure_ascii=False,
                )
                temporary.write("\n")

            os.chmod(temp_path, 0o600)
            os.replace(temp_path, destination)
            return destination
        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise
