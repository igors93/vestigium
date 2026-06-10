from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_uncaught_error_creates_forensic_snapshot(tmp_path):
    snapshot_directory = tmp_path / "snapshots"

    code = f"""
from vestigium import configure, context, event

configure(
    project_name="integration-test",
    snapshot_directory={str(snapshot_directory)!r},
)

def fail():
    password = "super-secret"
    price = "100"
    discount = 10
    return price - discount

with context("calculate_total", order_id="ord-1"):
    event("calculation_started")
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

    json_snapshots = list(snapshot_directory.glob("*.json"))
    assert len(json_snapshots) == 1

    snapshot = json.loads(json_snapshots[0].read_text(encoding="utf-8"))

    assert snapshot["schema_version"] == "1.0"
    assert snapshot["incident"]["type"] == "exception"
    assert snapshot["incident"]["operation"] == "calculate_total"
    assert snapshot["exception"]["type"] == "TypeError"
    assert snapshot["exception"]["traceback"][-1]["locals"]["password"] == "[SECRET]"
    assert snapshot["exception"]["traceback"][-1]["locals"]["price"] == "100"
    assert snapshot["events"][0]["name"] == "calculation_started"
