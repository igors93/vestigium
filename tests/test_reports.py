from __future__ import annotations

from vestigium import anomaly, capture_exception, configure, context, event
from vestigium.reports.text_report import render_text_snapshot


def test_render_text_snapshot_contains_factual_sections(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    with context("process_order", order_id="ord-1"):
        event("order_validated")
        snapshot = anomaly("unexpected_order_state")

    rendered = render_text_snapshot(snapshot)

    assert "VESTIGIUM FORENSIC SNAPSHOT" in rendered
    assert "Incident: anomaly/unexpected_order_state" in rendered
    assert "Operation: process_order" in rendered
    assert "order_validated" in rendered


def test_render_text_snapshot_supports_exception(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    try:
        raise ValueError("invalid value")
    except ValueError as error:
        snapshot = capture_exception(error)

    rendered = render_text_snapshot(snapshot)

    assert "EXCEPTION" in rendered
    assert "ValueError" in rendered
    assert "invalid value" in rendered


def test_render_text_snapshot_supports_empty_events(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    snapshot = anomaly("manual_without_events")

    assert "No events were recorded." in render_text_snapshot(snapshot)
