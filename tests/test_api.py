from __future__ import annotations

import sys

import pytest

from vestigium import (
    InvariantViolation,
    anomaly,
    capture,
    configure,
    context,
    event,
    invariant,
    start,
    stop,
    trace,
    unexpected_result,
)
from vestigium.config import Config


def test_configure_returns_config_and_can_install_excepthook(tmp_path, memory_store):
    original_hook = sys.excepthook

    try:
        config = configure(
            project_name="api-test",
            snapshot_directory=str(tmp_path),
            application_version="1.2.3",
            store=memory_store,
        )

        assert isinstance(config, Config)
        assert config.project_name == "api-test"
        assert config.application_version == "1.2.3"
        assert sys.excepthook is not original_hook
    finally:
        stop()

    assert sys.excepthook is original_hook


def test_start_remains_compatibility_wrapper(tmp_path):
    config = start(
        project_name="legacy-api",
        reports_directory=str(tmp_path),
        capture_locals=False,
    )

    assert config.project_name == "legacy-api"
    assert config.snapshot_path == tmp_path
    assert config.capture_locals is False


def test_anomaly_persists_snapshot_with_context_and_event(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    with context("process_payment", order_id="ord_123"):
        event("payment_requested", provider="gateway")
        snapshot = anomaly(
            "approved_payment_without_transaction_id",
            expected={"transaction_id": "non-empty"},
            actual={"transaction_id": None},
        )

    assert snapshot is not None
    assert len(memory_store.snapshots) == 1
    assert snapshot.incident.type == "anomaly"
    assert snapshot.incident.operation == "process_payment"
    assert snapshot.context.active[0]["data"]["order_id"] == "ord_123"
    assert [event.name for event in snapshot.events] == ["payment_requested"]


def test_invariant_captures_and_can_raise(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    snapshot = invariant(
        False,
        "balance_must_not_be_negative",
        expected={"balance": ">= 0"},
        actual={"balance": -10},
    )

    assert snapshot is not None
    assert snapshot.incident.type == "invariant_violation"

    with pytest.raises(InvariantViolation):
        invariant(False, "raise_after_capture", raise_on_failure=True)


def test_unexpected_result_uses_its_own_incident_type(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    snapshot = unexpected_result(
        "missing_invoice_id",
        expected={"invoice_id": "non-empty"},
        actual={"invoice_id": None},
    )

    assert snapshot is not None
    assert snapshot.incident.type == "unexpected_result"


def test_manual_capture_and_origin_are_recorded(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    snapshot = capture("operator_requested_snapshot", metadata={"ticket": "INC-1"})

    assert snapshot is not None
    assert snapshot.incident.type == "manual_capture"
    assert snapshot.incident.origin is not None
    assert (
        snapshot.incident.origin.function
        == "test_manual_capture_and_origin_are_recorded"
    )
    assert snapshot.incident.metadata["ticket"] == "INC-1"


def test_trace_decorator_wraps_function_in_context(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    @trace("decorated_operation", job_id="job-1")
    def run_job() -> None:
        event("job_started")
        anomaly("job_anomaly")

    run_job()

    snapshot = memory_store.snapshots[0]
    assert snapshot.incident.operation == "decorated_operation"
    assert snapshot.context.active[0]["data"]["job_id"] == "job-1"
