from __future__ import annotations

import sys

from vestigium import start, stop
from vestigium.config import Config


def test_start_returns_config_and_installs_handler(tmp_path):
    original_hook = sys.excepthook

    try:
        config = start(
            project_name="api-test",
            reports_directory=str(tmp_path),
            capture_locals=False,
        )

        assert isinstance(config, Config)
        assert config.project_name == "api-test"
        assert config.capture_locals is False
        assert sys.excepthook is not original_hook
    finally:
        stop()

    assert sys.excepthook is original_hook
