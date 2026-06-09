from src.config import Config
from src.models.report import ErrorReport
from src.reports.text_report import render_text_report, save_text_report


def test_render_text_report_contains_main_sections(
    sample_report: ErrorReport,
):
    rendered = render_text_report(sample_report)

    assert "VESTIGIUM ERROR REPORT" in rendered
    assert "ValueError" in rendered
    assert "invalid value" in rendered
    assert "password = <redacted>" in rendered
    assert "app.py:10" in rendered


def test_render_text_report_supports_missing_line(
    sample_report: ErrorReport,
):
    frame = sample_report.frames[0]
    report = ErrorReport(
        error_id=sample_report.error_id,
        project_name=sample_report.project_name,
        captured_at=sample_report.captured_at,
        exception_type=sample_report.exception_type,
        exception_message=sample_report.exception_message,
        frames=[
            type(frame)(
                file=frame.file,
                line=None,
                function=frame.function,
                source=frame.source,
            )
        ],
        local_variables=sample_report.local_variables,
        environment=sample_report.environment,
    )

    assert "app.py:unknown" in render_text_report(report)


def test_save_text_report_creates_file(
    tmp_path,
    sample_report: ErrorReport,
):
    destination = save_text_report(
        sample_report,
        Config(reports_directory=str(tmp_path)),
    )

    assert destination.exists()
    assert destination.read_text(encoding="utf-8").startswith("VESTIGIUM ERROR REPORT")
