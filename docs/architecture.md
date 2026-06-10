# Architecture

Vestigium is organized around one rule: persist structured forensic
evidence only when an incident is triggered.

## Public API

`src/vestigium/api.py` exposes the small progressive API:

- `configure()`;
- `context()`;
- `event()`;
- `anomaly()`;
- `invariant()`;
- `unexpected_result()`;
- `capture()`;
- `capture_exception()`;
- `trace()`.

`start()` and `stop()` remain compatibility wrappers.

## Runtime State

`src/vestigium/runtime.py` keeps active logical contexts and recent events
in a `contextvars.ContextVar`. Normal execution stores only bounded
sanitized evidence in memory. Top-level context exit discards events when
no incident happened.

## Incidents

`src/vestigium/incidents/models.py` defines `IncidentInput`, the raw
capture request created by the API. Supported incident types are:

- `exception`;
- `anomaly`;
- `invariant_violation`;
- `unexpected_result`;
- `manual_capture`.

## Snapshots

`src/vestigium/snapshots/models.py` defines the versioned persisted schema.
`src/vestigium/snapshots/builder.py` converts an incident plus current
runtime state into a sanitized `Snapshot`.

The snapshot separates:

- incident;
- exception;
- execution;
- context;
- events;
- reproduction facts;
- environment;
- application;
- limitations;
- privacy.

## Privacy

`src/vestigium/privacy/adapter.py` is the only sanitization boundary used
by Vestigium. It bounds structure depth, collection size, and value length,
then delegates detection and masking to LogPrivacy. Sanitizer failures
produce safe markers instead of leaking original values.

## Persistence

`src/vestigium/storage/base.py` defines `SnapshotStore`.
`src/vestigium/storage/json_store.py` implements local JSON storage with
atomic writes. Capture code depends on the protocol, not on JSON directly.

## Integrations

`src/vestigium/integrations/excepthook.py` captures uncaught exceptions
through `sys.excepthook` and always calls the original hook afterward.

## Design Rules

- Record evidence, not opinions.
- Never hide the application exception.
- Never persist unsanitized data.
- Keep normal execution bounded and in memory.
- Do not implement retry, fallback, circuit breaking, automatic repair,
  automatic replay, continuous logging, or causal diagnosis.
