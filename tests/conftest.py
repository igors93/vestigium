from __future__ import annotations

import pytest

from vestigium.models.report import ErrorReport, FrameInfo


@pytest.fixture
def sample_report() -> ErrorReport:
    return ErrorReport(
        error_id="err-20260608-120000-abc12345",
        project_name="test-project",
        captured_at="2026-06-08T12:00:00+00:00",
        exception_type="ValueError",
        exception_message="invalid value",
        frames=[
            FrameInfo(
                file="app.py",
                line=10,
                function="run",
                source="raise ValueError('invalid value')",
            )
        ],
        local_variables={
            "value": "'bad'",
            "password": "<redacted>",
        },
        environment={
            "python_version": "3.10.0",
            "operating_system": "Test OS",
            "working_directory": "/tmp/project",
        },
    )
