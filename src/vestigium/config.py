from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Config:
    project_name: str = "python-project"
    reports_directory: str = ".reports"
    capture_locals: bool = True
    max_value_length: int = 500

    @property
    def reports_path(self) -> Path:
        return Path(self.reports_directory)
