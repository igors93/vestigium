from __future__ import annotations

import sys
from types import TracebackType

import pytest
import src.core.handler as handler_module
from src.config import Config
from src.core.handler import install_handler, uninstall_handler


@pytest.fixture(autouse=True)
def restore_exception_handler():
    original_hook = sys.excepthook
    uninstall_handler()

    yield

    uninstall_handler()
    sys.excepthook = original_hook


def test_install_handler_is_idempotent(monkeypatch, tmp_path):
    def original_hook(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
    ) -> None:
        return None

    monkeypatch.setattr(sys, "excepthook", original_hook)

    install_handler(Config(reports_directory=str(tmp_path)))
    installed_hook = sys.excepthook
    install_handler(Config(reports_directory=str(tmp_path / "other")))

    assert sys.excepthook is installed_hook


def test_handler_creates_reports_and_calls_original(monkeypatch, tmp_path):
    calls: list[str] = []

    def original_hook(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
    ) -> None:
        calls.append(exception_type.__name__)

    monkeypatch.setattr(sys, "excepthook", original_hook)
    install_handler(Config(reports_directory=str(tmp_path)))

    try:
        local_value = "captured"
        raise RuntimeError(local_value)
    except RuntimeError as error:
        sys.excepthook(type(error), error, error.__traceback__)

    assert calls == ["RuntimeError"]
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert len(list(tmp_path.glob("*.txt"))) == 1


def test_recording_failure_does_not_hide_original_error(
    monkeypatch,
    tmp_path,
):
    calls: list[str] = []

    def original_hook(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
    ) -> None:
        calls.append(str(exception))

    def fail_to_build_report(*args, **kwargs):
        raise OSError("storage unavailable")

    monkeypatch.setattr(sys, "excepthook", original_hook)
    monkeypatch.setattr(
        handler_module,
        "build_report",
        fail_to_build_report,
    )
    install_handler(Config(reports_directory=str(tmp_path)))

    error = ValueError("original failure")
    sys.excepthook(ValueError, error, None)

    assert calls == ["original failure"]
