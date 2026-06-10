from pathlib import Path

import pytest

from vestigium.config import Config


def test_snapshot_path_returns_path_object(tmp_path):
    config = Config(snapshot_directory=str(tmp_path / "snapshots"))

    assert config.snapshot_path == Path(tmp_path / "snapshots")


def test_limits_must_be_non_negative():
    with pytest.raises(ValueError, match="event_limit"):
        Config(event_limit=-1)
