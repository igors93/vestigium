from __future__ import annotations

import json
import os

import pytest

from vestigium import anomaly, configure, context, event
from vestigium.storage.json_store import JsonSnapshotStore


def test_json_store_creates_valid_versioned_snapshot(tmp_path, memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)
    with context("generate_invoice", invoice_id="inv-1"):
        event("invoice_loaded")
        snapshot = anomaly("invoice_total_mismatch")

    store = JsonSnapshotStore(tmp_path / "nested")
    destination = store.save(snapshot)
    data = json.loads(destination.read_text(encoding="utf-8"))

    assert destination.exists()
    assert data["schema_version"] == "1.0"
    assert data["incident"]["id"] == snapshot.incident.id
    assert data["context"]["operation"] == "generate_invoice"
    assert data["privacy"]["engine"] == "logprivacy"


def test_json_store_uses_atomic_replace_and_cleans_temp_on_error(
    monkeypatch,
    tmp_path,
    memory_store,
):
    configure(store=memory_store, capture_uncaught_exceptions=False)
    snapshot = anomaly("disk_test")

    def fail_replace(*args, **kwargs):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        JsonSnapshotStore(tmp_path).save(snapshot)

    assert list(tmp_path.glob("*.tmp")) == []


def test_normal_context_and_events_are_not_persisted(tmp_path):
    configure(
        snapshot_directory=str(tmp_path),
        capture_uncaught_exceptions=False,
    )

    with context("normal_operation"):
        event("step_completed")

    assert list(tmp_path.glob("*.json")) == []
