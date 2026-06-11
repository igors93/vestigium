from __future__ import annotations

import sys
from types import TracebackType

import pytest

from tests.conftest import FailingStore
from vestigium import capture_exception, configure, context, event, stop


def _raise_always(*args: object, **kwargs: object) -> object:
    raise RuntimeError("internal crash")


def test_capture_exception_records_traceback_and_chain(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    try:
        try:
            raise ValueError("token=abc123456789")
        except ValueError as cause:
            raise RuntimeError("wrapped failure") from cause
    except RuntimeError as error:
        snapshot = capture_exception(error)

    assert snapshot is not None
    assert snapshot.exception is not None
    assert snapshot.incident.type == "exception"
    assert snapshot.exception.type == "RuntimeError"
    assert snapshot.exception.chain[0]["type"] == "ValueError"
    assert "[SECRET]" in snapshot.exception.chain[0]["message"]
    assert snapshot.exception.traceback


def test_context_exception_is_captured_and_original_is_preserved(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    with pytest.raises(RuntimeError, match="original failure"):
        with context("dangerous_operation"):
            event("before_failure")
            raise RuntimeError("original failure")

    snapshot = memory_store.snapshots[0]
    assert snapshot.incident.source == "context_manager"
    assert snapshot.exception is not None
    assert snapshot.exception.message == "original failure"
    assert [event.name for event in snapshot.events] == ["before_failure"]


def test_excepthook_creates_snapshot_and_calls_original(monkeypatch, memory_store):
    calls: list[str] = []

    def original_hook(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
    ) -> None:
        calls.append(exception_type.__name__)

    monkeypatch.setattr(sys, "excepthook", original_hook)
    configure(store=memory_store)

    try:
        raise RuntimeError("uncaught")
    except RuntimeError as error:
        sys.excepthook(type(error), error, error.__traceback__)

    assert calls == ["RuntimeError"]
    assert len(memory_store.snapshots) == 1
    assert memory_store.snapshots[0].incident.source == "sys.excepthook"


def test_capture_failure_does_not_replace_application_exception():
    configure(store=FailingStore(), capture_uncaught_exceptions=False)
    error = ValueError("original")

    snapshot = capture_exception(error)

    assert snapshot is not None
    assert str(error) == "original"
    stop()


def test_build_failure_returns_none_without_raising(monkeypatch, memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)
    monkeypatch.setattr("vestigium.api.build_snapshot", _raise_always)

    result = capture_exception(ValueError("original"))

    assert result is None


def test_original_exception_preserved_when_snapshot_build_fails_in_context(
    monkeypatch, memory_store
):
    configure(store=memory_store, capture_uncaught_exceptions=False)
    monkeypatch.setattr("vestigium.api.build_snapshot", _raise_always)

    with pytest.raises(ValueError, match="original"):
        with context("operation"):
            raise ValueError("original")


def test_nested_contexts_create_one_snapshot_per_exception(memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)

    with pytest.raises(RuntimeError):
        with context("outer"):
            with context("inner"):
                raise RuntimeError("failure")

    assert len(memory_store.snapshots) == 1


def test_event_silently_absorbs_internal_failure(monkeypatch, memory_store):
    configure(store=memory_store, capture_uncaught_exceptions=False)
    monkeypatch.setattr("vestigium.api.record_event", _raise_always)

    event("breadcrumb")


def test_persistence_failure_is_reported_to_stderr(capsys):
    configure(store=FailingStore(), capture_uncaught_exceptions=False)

    capture_exception(ValueError("test"))

    assert "[Vestigium]" in capsys.readouterr().err
