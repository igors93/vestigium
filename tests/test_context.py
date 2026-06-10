from __future__ import annotations

from vestigium.config import Config
from vestigium.core.context import build_report
from vestigium.models.report import ErrorReport


def _create_report(capture_locals: bool = True) -> ErrorReport:
    try:
        password = "private"  # noqa: F841
        value = "invalid"  # noqa: F841
        raise ValueError("broken input")
    except ValueError as error:
        return build_report(
            exception_type=type(error),
            exception=error,
            traceback_object=error.__traceback__,
            config=Config(
                project_name="context-test",
                capture_locals=capture_locals,
            ),
        )


def _create_nested_report() -> ErrorReport:
    def fail() -> None:
        token = "abc123456789"  # noqa: F841
        raise ValueError("nested failure")

    try:
        fail()
    except ValueError as error:
        return build_report(
            exception_type=type(error),
            exception=error,
            traceback_object=error.__traceback__,
            config=Config(project_name="context-test"),
        )


def _create_sensitive_text_report() -> ErrorReport:
    try:
        raise ValueError("email=ana@example.com password=123456")
    except ValueError as error:
        return build_report(
            exception_type=type(error),
            exception=error,
            traceback_object=error.__traceback__,
            config=Config(project_name="context-test"),
        )


class BrokenStrError(Exception):
    def __str__(self) -> str:
        raise RuntimeError("cannot render")


def test_build_report_captures_error_context():
    report = _create_report()

    assert report.project_name == "context-test"
    assert report.exception_type == "ValueError"
    assert report.exception_message == "broken input"
    assert report.frames[-1].function == "_create_report"
    assert report.local_variables["password"] == "<redacted>"
    assert report.local_variables["value"] == "'invalid'"
    assert "python_version" in report.environment


def test_build_report_captures_locals_from_failing_frame():
    report = _create_nested_report()

    assert [frame.function for frame in report.frames][-2:] == [
        "_create_nested_report",
        "fail",
    ]
    assert report.local_variables["token"] == "<redacted>"


def test_build_report_sanitizes_exception_message_and_source():
    report = _create_sensitive_text_report()
    source = report.frames[-1].source

    assert report.exception_message == "email=[EMAIL] password=[SECRET]"
    assert source is not None
    assert "[EMAIL]" in source
    assert "[SECRET]" in source
    assert "ana@example.com" not in source
    assert "123456" not in source


def test_build_report_handles_broken_exception_message():
    report = build_report(
        exception_type=BrokenStrError,
        exception=BrokenStrError(),
        traceback_object=None,
        config=Config(),
    )

    assert report.exception_message == "<BrokenStrError: unavailable>"


def test_build_report_can_disable_local_capture():
    report = _create_report(capture_locals=False)

    assert report.local_variables == {}


def test_build_report_accepts_missing_traceback():
    report = build_report(
        exception_type=RuntimeError,
        exception=RuntimeError("missing traceback"),
        traceback_object=None,
        config=Config(),
    )

    assert report.frames == []
    assert report.local_variables == {}
