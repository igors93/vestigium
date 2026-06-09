from __future__ import annotations

from src.config import Config
from src.core.context import build_report
from src.models.report import ErrorReport


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


def test_build_report_captures_error_context():
    report = _create_report()

    assert report.project_name == "context-test"
    assert report.exception_type == "ValueError"
    assert report.exception_message == "broken input"
    assert report.frames[-1].function == "_create_report"
    assert report.local_variables["password"] == "<redacted>"
    assert report.local_variables["value"] == "'invalid'"
    assert "python_version" in report.environment


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
