from __future__ import annotations

from threading import Thread

from vestigium import anomaly, configure, context, event
from vestigium.runtime import get_state


def test_context_is_cleaned_after_normal_exit(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    with context("create_order", order_id="ord-1"):
        event("order_loaded")

    assert get_state().contexts == ()
    assert get_state().events == ()
    assert memory_store.snapshots == []


def test_nested_contexts_are_represented_in_snapshot(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    with context("handle_request", request_id="req-1"):
        event("request_received")
        with context("process_payment", payment_id="pay-1"):
            event("provider_called")
            snapshot = anomaly("provider_answered_without_id")

    assert snapshot is not None
    assert [frame["name"] for frame in snapshot.context.active] == [
        "handle_request",
        "process_payment",
    ]
    assert [event.name for event in snapshot.events] == [
        "request_received",
        "provider_called",
    ]


def test_event_buffer_is_circular(memory_store):
    configure(
        store=memory_store,
        event_limit=2,
        capture_uncaught_exceptions=False,
    )

    with context("sync_inventory"):
        event("step_1")
        event("step_2")
        event("step_3")
        snapshot = anomaly("inventory_mismatch")

    assert snapshot is not None
    assert [event.name for event in snapshot.events] == ["step_2", "step_3"]
    assert "event_buffer_truncated" in snapshot.limitations


def test_contextvars_isolate_threads(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    def run(worker_id: str) -> None:
        with context("worker", worker_id=worker_id):
            event("started", worker_id=worker_id)
            anomaly("worker_anomaly", actual={"worker_id": worker_id})

    threads = [Thread(target=run, args=(f"worker-{index}",)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    worker_ids = {
        snapshot.context.active[0]["data"]["worker_id"]
        for snapshot in memory_store.snapshots
    }
    event_worker_ids = {
        snapshot.events[0].data["worker_id"] for snapshot in memory_store.snapshots
    }

    assert worker_ids == {"worker-0", "worker-1"}
    assert event_worker_ids == {"worker-0", "worker-1"}
