from __future__ import annotations

from vestigium import anomaly, configure, context, event


def test_snapshot_contains_reproduction_facts_and_limitations(memory_store):
    configure(
        application_version="2.0.0",
        store=memory_store,
        max_value_length=20,
        capture_uncaught_exceptions=False,
    )

    with context("ship_order", order_id="order-12345678901234567890"):
        event("label_created", tracking_number="TRACK-12345678901234567890")
        snapshot = anomaly(
            "shipment_without_carrier",
            expected={"carrier": "non-empty"},
            actual={"carrier": None},
        )

    assert snapshot is not None
    assert snapshot.reproduction["operation"] == "ship_order"
    assert snapshot.reproduction["application_version"] == "2.0.0"
    assert snapshot.reproduction["event_names"] == ["label_created"]
    assert "value_truncated" in snapshot.limitations
