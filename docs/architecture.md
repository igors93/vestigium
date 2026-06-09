# Architecture

Vestigium separates each responsibility into a small module.

## `src/api.py`

Provides the public API:

- `start()` enables error capture;
- `stop()` restores the previous Python exception handler.

## `src/core/handler.py`

Connects Vestigium to `sys.excepthook`. It coordinates report creation and
always calls the original exception handler afterward.

## `src/core/context.py`

Converts an exception and its traceback into a structured `ErrorReport`.

## `src/core/sanitizer.py`

Converts local values to safe strings, limits their size, and redacts
sensitive variable names.

## `src/models/report.py`

Defines the data structures used by the rest of the project.

## `src/reports/`

Creates formats intended for human reading.

## `src/storage/`

Saves structured data. The current implementation uses JSON files.

## `src/integrations/`

Reserved for future integrations with frameworks and testing tools.

## Design rules

- Recording failures must never hide the original application exception.
- Sensitive information must be removed before persistence.
- Storage and formatting remain independent from context collection.
- Public APIs remain small while internal modules can evolve.
