# Usage

Vestigium is configured once near the application entry point.

```python
from vestigium import configure

configure(
    project_name="my-application",
    snapshot_directory=".vestigium",
    application_version="1.4.0",
)
```

## Logical Context

Use `context()` to describe the operation currently in progress.
Contexts may be nested and are isolated with `contextvars`.

```python
from vestigium import context

with context("handle_request", request_id=request.id):
    with context("create_order", order_id=order.id):
        ...
```

Context data is bounded and sanitized before it can be persisted.

## Breadcrumb Events

Use `event()` for important execution steps. Events are held in a bounded
in-memory buffer and are not written during normal execution.

```python
from vestigium import event

event("order_validated", item_count=len(order.items))
```

When the event limit is reached, Vestigium keeps the most recent events
and records an `event_buffer_truncated` limitation in the next snapshot.

## Triggering Incidents

### Anomaly

```python
from vestigium import anomaly

anomaly(
    "approved_payment_without_transaction_id",
    expected={"transaction_id": "non-empty"},
    actual={"transaction_id": None},
)
```

### Invariant

```python
from vestigium import invariant

invariant(
    account.balance >= 0,
    "account_balance_must_not_be_negative",
    expected={"balance": ">= 0"},
    actual={"balance": account.balance},
)
```

By default, `invariant()` captures evidence and lets the application
continue. Pass `raise_on_failure=True` to raise `InvariantViolation` after
the snapshot attempt.

### Explicit Exception

```python
from vestigium import capture_exception

try:
    process()
except Exception as error:
    capture_exception(error)
    raise
```

## Snapshot Files

Default JSON snapshots are written to `.vestigium/`:

```text
.vestigium/
└── inc-20260610-120000-ab12cd34.json
```

The JSON schema is versioned and separates incident, exception, execution,
context, events, reproduction facts, environment, application data,
limitations, and privacy metadata.

## Privacy

Vestigium uses LogPrivacy as its official sanitization engine. Before
persistence, it sanitizes exception messages, traceback source lines,
locals, context data, events, expected and actual states, metadata, URLs,
and configuration-like values. If sanitization fails, Vestigium replaces
the affected value with a safe marker.

## Migration

The old `start(project_name=..., reports_directory=...)` API remains as a
compatibility wrapper around `configure()`, but new code should use:

```python
from vestigium import configure

configure(project_name="my-application", snapshot_directory=".vestigium")
```

Vestigium now writes one structured JSON snapshot by default. Text output
is available through `vestigium.reports.render_text_snapshot()` when a
caller wants a readable summary.
