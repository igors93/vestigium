from __future__ import annotations

import sys
from collections.abc import Callable
from types import TracebackType

from vestigium.config import Config

ExceptionHook = Callable[
    [type[BaseException], BaseException, TracebackType | None],
    None,
]

_HANDLER_MARKER = "__vestigium_installed__"
_original_hook: ExceptionHook | None = None
_active_config: Config | None = None


def install_excepthook(config: Config) -> None:
    """Install automatic uncaught-exception snapshot capture."""

    global _active_config, _original_hook

    _active_config = config
    if getattr(sys.excepthook, _HANDLER_MARKER, False):
        return

    _original_hook = sys.excepthook

    def error_hook(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
    ) -> None:
        try:
            from vestigium.api import capture_exception

            capture_exception(
                exception,
                source="sys.excepthook",
                origin_skip=2,
            )
        except Exception as capture_error:
            print(
                f"[Vestigium] Failed to create snapshot: {capture_error}",
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


def uninstall_excepthook() -> None:
    """Restore the exception hook that existed before Vestigium installed one."""

    global _active_config, _original_hook

    if getattr(sys.excepthook, _HANDLER_MARKER, False) and _original_hook is not None:
        sys.excepthook = _original_hook

    _original_hook = None
    _active_config = None
