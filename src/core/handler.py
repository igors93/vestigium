from __future__ import annotations

import sys
from collections.abc import Callable
from types import TracebackType

from src.config import Config
from src.reports.text_report import save_text_report
from src.storage.json_store import save_json_report

from .context import build_report

ExceptionHook = Callable[
    [type[BaseException], BaseException, TracebackType | None],
    None,
]

_HANDLER_MARKER = "__vestigium_installed__"
_original_hook: ExceptionHook | None = None


def install_handler(config: Config) -> None:
    """Install a global handler for uncaught exceptions."""

    global _original_hook

    if getattr(sys.excepthook, _HANDLER_MARKER, False):
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
                f"\n[Vestigium] Captured error: {report.error_id}",
                file=sys.stderr,
            )
            print(f"[Vestigium] JSON report: {json_path}", file=sys.stderr)
            print(f"[Vestigium] Text report: {text_path}\n", file=sys.stderr)
        except Exception as capture_error:
            # Recording failures must never hide the original exception.
            print(
                f"[Vestigium] Failed to create report: {capture_error}",
                file=sys.stderr,
            )
        finally:
            if _original_hook is not None:
                _original_hook(
                    exception_type,
                    exception,
                    traceback_object,
                )

    setattr(error_hook, _HANDLER_MARKER, True)
    sys.excepthook = error_hook


def uninstall_handler() -> None:
    """Restore the original exception handler when Vestigium owns it."""

    global _original_hook

    if not getattr(sys.excepthook, _HANDLER_MARKER, False):
        _original_hook = None
        return

    if _original_hook is not None:
        sys.excepthook = _original_hook

    _original_hook = None
