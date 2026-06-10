from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_uncaught_error_creates_reports(tmp_path):
    reports_directory = tmp_path / "reports"

    code = f"""
from vestigium import start

start(
    project_name="integration-test",
    reports_directory={str(reports_directory)!r},
)

def fail():
    password = "super-secret"
    price = "100"
    discount = 10
    return price - discount

fail()
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0

    json_reports = list(reports_directory.glob("*.json"))
    text_reports = list(reports_directory.glob("*.txt"))

    assert len(json_reports) == 1
    assert len(text_reports) == 1

    report = json.loads(json_reports[0].read_text(encoding="utf-8"))

    assert report["exception_type"] == "TypeError"
    assert report["local_variables"]["password"] == "<redacted>"
    assert report["local_variables"]["price"] == "'100'"
    assert report["local_variables"]["discount"] == "10"
