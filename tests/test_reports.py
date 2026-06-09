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


def test_save_text_report_creates_file(
    tmp_path,
    sample_report: ErrorReport,
):
    destination = save_text_report(
        sample_report,
        Config(reports_directory=str(tmp_path)),
    )

    assert destination.exists()
    assert destination.read_text(encoding="utf-8").startswith(
        "VESTIGIUM ERROR REPORT"
    )
