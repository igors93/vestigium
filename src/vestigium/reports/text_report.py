from __future__ import annotations

from vestigium.snapshots.models import Snapshot


def render_text_snapshot(snapshot: Snapshot) -> str:
    """Render a snapshot as a compact human-readable forensic summary."""

    lines = [
        "VESTIGIUM FORENSIC SNAPSHOT",
        "=" * 50,
        f"Schema: {snapshot.schema_version}",
        f"Incident ID: {snapshot.incident.id}",
        f"Incident: {snapshot.incident.type}/{snapshot.incident.name}",
        f"Severity: {snapshot.incident.severity}",
        f"Captured at: {snapshot.incident.captured_at}",
        f"Operation: {snapshot.incident.operation or 'unknown'}",
        "",
        "FACTS",
        "-" * 50,
        f"Source: {snapshot.incident.source}",
    ]

    if snapshot.incident.message:
        lines.append(f"Message: {snapshot.incident.message}")

    if snapshot.exception is not None:
        lines.extend(
            [
                "",
                "EXCEPTION",
                "-" * 50,
                f"Type: {snapshot.exception.type}",
                f"Message: {snapshot.exception.message}",
            ]
        )
        for index, frame in enumerate(snapshot.exception.traceback, start=1):
            line = frame.line if frame.line is not None else "unknown"
            lines.append(f"{index}. {frame.function} ({frame.file}:{line})")
            if frame.source:
                lines.append(f"   Code: {frame.source}")

    lines.extend(["", "EVENTS", "-" * 50])
    if snapshot.events:
        for event in snapshot.events:
            lines.append(f"{event.sequence}. {event.name} @ {event.recorded_at}")
    else:
        lines.append("No events were recorded.")

    if snapshot.limitations:
        lines.extend(["", "LIMITATIONS", "-" * 50, *snapshot.limitations])

    return "\n".join(lines)
