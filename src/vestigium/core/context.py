from __future__ import annotations

import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from types import TracebackType

from vestigium.config import Config
from vestigium.models.report import ErrorReport, FrameInfo
from vestigium.utils.identifiers import create_error_id

from .sanitizer import sanitize_mapping, sanitize_text


def build_report(
    exception_type: type[BaseException],
    exception: BaseException,
    traceback_object: TracebackType | None,
    config: Config,
) -> ErrorReport:
    """Build a structured report from an uncaught exception."""

    return ErrorReport(
        error_id=create_error_id(),
        project_name=config.project_name,
        captured_at=datetime.now(timezone.utc).isoformat(),
        exception_type=exception_type.__name__,
        exception_message=_extract_exception_message(exception),
        frames=_extract_frames(traceback_object),
        local_variables=_extract_locals(traceback_object, config),
        environment={
            "python_version": sys.version.split()[0],
            "operating_system": platform.platform(),
            "working_directory": os.getcwd(),
        },
    )


def _extract_frames(
    traceback_object: TracebackType | None,
) -> list[FrameInfo]:
    if traceback_object is None:
        return []

    return [
        FrameInfo(
            file=frame.filename,
            line=frame.lineno,
            function=frame.name,
            source=sanitize_text(frame.line) if frame.line is not None else None,
        )
        for frame in traceback.extract_tb(traceback_object)
    ]


def _extract_exception_message(exception: BaseException) -> str:
    try:
        message = str(exception)
    except Exception:
        return f"<{type(exception).__name__}: unavailable>"

    return sanitize_text(message)


def _extract_locals(
    traceback_object: TracebackType | None,
    config: Config,
) -> dict[str, str]:
    if traceback_object is None or not config.capture_locals:
        return {}

    last_traceback = traceback_object
    while last_traceback.tb_next is not None:
        last_traceback = last_traceback.tb_next

    return sanitize_mapping(
        last_traceback.tb_frame.f_locals,
        max_length=config.max_value_length,
    )
