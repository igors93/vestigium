from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def create_error_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = uuid4().hex[:8]
    return f"err-{timestamp}-{suffix}"
