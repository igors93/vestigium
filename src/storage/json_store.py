from __future__ import annotations

import json
from pathlib import Path

from src.config import Config
from src.models.report import ErrorReport


def save_json_report(
    report: ErrorReport,
    config: Config,
) -> Path:
    """Save a structured JSON report and return its path."""

    config.reports_path.mkdir(parents=True, exist_ok=True)
    destination = config.reports_path / f"{report.error_id}.json"
    destination.write_text(
        json.dumps(
            report.to_dict(),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return destination
