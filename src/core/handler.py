from __future__ import annotations

import sys
from types import TracebackType
from typing import Callable

from src.config import Config
from src.reports.text_report import save_text_report
from src.storage.json_store import save_json_report

from .context import build_report


ExceptionHook = Callable[
    [type[BaseException], BaseException, TracebackType | None],
    object,
]

_original_hook: ExceptionHook | None = None


def install_handler(config: Config) -> None:
    """Install a global handler for uncaught exceptions."""

    global _original_hook

    if getattr(sys.excepthook, "__recorder_installed__", False):
        return

    _original_hook = sys.excepthook

    def error_hook(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
    ) -> None:
        try:
            report = build_report(
                exception_type=exception_type,
                exception=exception,
                traceback_object=traceback_object,
                config=config,
            )
            json_path = save_json_report(report, config)
            text_path = save_text_report(report, config)

            print(
                f"\n[Recorder] Captured error: {report.error_id}",
                file=sys.stderr,
            )
            print(f"[Recorder] JSON report: {json_path}", file=sys.stderr)
            print(f"[Recorder] Text report: {text_path}\n", file=sys.stderr)
        except Exception as capture_error:
            # Error recording must never hide the original exception.
            print(
                f"[Recorder] Failed to create report: {capture_error}",
                file=sys.stderr,
            )
        finally:
            if _original_hook is not None:
                _original_hook(
                    exception_type,
                    exception,
                    traceback_object,
                )

    setattr(error_hook, "__recorder_installed__", True)
    sys.excepthook = error_hook
