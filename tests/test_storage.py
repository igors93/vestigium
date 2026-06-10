import json

from vestigium.config import Config
from vestigium.models.report import ErrorReport
from vestigium.storage.json_store import save_json_report


def test_save_json_report_creates_valid_json(
    tmp_path,
    sample_report: ErrorReport,
):
    destination = save_json_report(
        sample_report,
        Config(reports_directory=str(tmp_path / "nested")),
    )

    data = json.loads(destination.read_text(encoding="utf-8"))

    assert destination.exists()
    assert data["error_id"] == sample_report.error_id
    assert data["exception_type"] == "ValueError"
    assert data["local_variables"]["password"] == "<redacted>"
