from __future__ import annotations

from .config import Config
from .core.handler import install_handler, uninstall_handler


def start(
    project_name: str = "python-project",
    reports_directory: str = ".reports",
    capture_locals: bool = True,
) -> Config:
    """Enable error capture for uncaught exceptions."""

    config = Config(
        project_name=project_name,
        reports_directory=reports_directory,
        capture_locals=capture_locals,
    )
    install_handler(config)
    return config


def stop() -> None:
    """Restore the exception handler that existed before start()."""

    uninstall_handler()
