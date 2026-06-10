from pathlib import Path

from vestigium.config import Config


def test_reports_path_returns_path_object(tmp_path):
    config = Config(reports_directory=str(tmp_path / "reports"))

    assert config.reports_path == Path(tmp_path / "reports")
