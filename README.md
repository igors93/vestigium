# Vestigium

Vestigium is an exception- and abnormal-behavior-triggered forensic
diagnostics library that produces structured snapshots for failure
reproduction and investigation.

It records factual evidence about an execution. It does not infer root
causes, propose fixes, retry operations, apply fallbacks, run circuit
breakers, stream continuous logs, or perform automatic replay.

## Problem

Production failures often disappear before a developer can inspect the
relevant state. Logs may be incomplete, noisy, or missing the operation
context needed to reproduce the issue. Vestigium keeps a small bounded
execution context in memory and persists it only when an incident is
explicitly triggered or an exception is captured.

## What It Captures

Snapshots can include:

- incident type, name, severity, origin, expected state, and observed state;
- active logical operation and nested context data;
- recent bounded breadcrumbs;
- exception type, message, traceback, chain, and failing-frame locals;
- environment and application version facts;
- reproduction hints based on factual data;
- limitations that describe truncated or incomplete capture;
- privacy metadata.

All persisted data is sanitized through LogPrivacy before it is written.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Minimal Usage

```python
from vestigium import configure

configure(project_name="my-application")
```

With this configuration, uncaught exceptions in the main process create
JSON snapshots in `.vestigium/`.

## Context And Anomaly

```python
from vestigium import anomaly, configure, context, event

configure(project_name="checkout")

with context("process_payment", order_id=order.id, customer_id=order.customer_id):
    event("payment_requested", provider=provider.name)
    result = provider.charge(order.total)
    event("payment_provider_answered", status=result.status)

    if result.status == "approved" and result.transaction_id is None:
        anomaly(
            "approved_payment_without_transaction_id",
            expected={"transaction_id": "non-empty"},
            actual={
                "status": result.status,
                "transaction_id": result.transaction_id,
            },
        )
```

Events are kept in a bounded in-memory buffer. They are discarded when no
incident happens.

## Explicit Exception Capture

```python
from vestigium import capture_exception

try:
    process()
except Exception as error:
    capture_exception(error)
    raise
```

Vestigium never swallows the original exception.

## Snapshot Shape

```json
{
  "schema_version": "1.0",
  "incident": {},
  "exception": {},
  "execution": {},
  "context": {},
  "events": [],
  "reproduction": {},
  "environment": {},
  "application": {},
  "limitations": [],
  "privacy": {}
}
```

## Project Structure

```text
src/vestigium/
├── api.py
├── config.py
├── incidents/
├── integrations/
├── privacy/
├── reports/
├── runtime.py
├── snapshots/
├── storage/
└── utils/
```

## Quality Checks

```bash
ruff check .
ruff format --check .
mypy src/vestigium
pytest --cov=vestigium --cov-report=term-missing
```

## Current Limitations

- Automatic capture currently focuses on `sys.excepthook`.
- Thread and asyncio integrations are not separate first-class modules yet.
- Snapshots are stored locally as JSON by default.
- Text rendering exists as an optional helper, not as core persistence.
- Vestigium records evidence; external people or tools perform diagnosis.
