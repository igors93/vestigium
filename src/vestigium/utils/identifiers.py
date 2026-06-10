from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def create_error_id() -> str:
    """Create a sortable identifier with a short random suffix."""

    return create_incident_id()


def create_incident_id() -> str:
    """Create a sortable incident identifier with a short random suffix."""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = uuid4().hex[:8]
    return f"inc-{timestamp}-{suffix}"
