from __future__ import annotations

from pathlib import Path

from src.config import Config
from src.models.report import ErrorReport


def save_text_report(
    report: ErrorReport,
    config: Config,
) -> Path:
    """Save a plain-text report and return its path."""

    config.reports_path.mkdir(parents=True, exist_ok=True)
    destination = config.reports_path / f"{report.error_id}.txt"
    destination.write_text(
        render_text_report(report),
        encoding="utf-8",
    )
    return destination


def render_text_report(report: ErrorReport) -> str:
    """Render a report in a readable plain-text format."""

    lines = [
        "VESTIGIUM ERROR REPORT",
        "=" * 50,
        f"Error ID: {report.error_id}",
        f"Project: {report.project_name}",
        f"Captured at: {report.captured_at}",
        "",
        "ERROR",
        "-" * 50,
        f"Type: {report.exception_type}",
        f"Message: {report.exception_message}",
        "",
        "TRACEBACK",
        "-" * 50,
    ]

    if report.frames:
        for index, frame in enumerate(report.frames, start=1):
            line = frame.line if frame.line is not None else "unknown"
            lines.append(f"{index}. {frame.function} ({frame.file}:{line})")
            if frame.source:
                lines.append(f"   Code: {frame.source}")
    else:
        lines.append("No traceback frames were captured.")

    lines.extend(["", "LOCAL VARIABLES", "-" * 50])

    if report.local_variables:
        for name, value in report.local_variables.items():
            lines.append(f"{name} = {value}")
    else:
        lines.append("No local variables were captured.")

    lines.extend(["", "ENVIRONMENT", "-" * 50])

    for name, value in report.environment.items():
        lines.append(f"{name}: {value}")

    lines.extend(
        [
            "",
            "NOTE",
            "-" * 50,
            "This report describes the failure context.",
            "Automatic replay is not part of this initial version.",
            "",
        ]
    )

    return "\n".join(lines)
