# Architecture

Vestigium separates each responsibility into a small module.

## `src/vestigium/api.py`

Provides the public API:

- `start()` enables error capture;
- `stop()` restores the previous Python exception handler.

## `src/vestigium/core/handler.py`

Connects Vestigium to `sys.excepthook`. It coordinates report creation and
always calls the original exception handler afterward.

## `src/vestigium/core/context.py`

Converts an exception and its traceback into a structured `ErrorReport`.

## `src/vestigium/core/sanitizer.py`

Converts local values to safe strings, limits their size, and redacts
sensitive variable names. Rendered values are also passed through
LogPrivacy so sensitive content can be masked even when the variable name
looks harmless.

The same text sanitizer is used for exception messages and traceback
source lines before reports are persisted.

## `src/vestigium/models/report.py`

Defines the data structures used by the rest of the project.

## `src/vestigium/reports/`

Creates formats intended for human reading.

## `src/vestigium/storage/`

Saves structured data. The current implementation uses JSON files.

## `src/vestigium/integrations/`

Reserved for future integrations with frameworks and testing tools.

## Design rules

- Recording failures must never hide the original application exception.
- Sensitive information must be removed before persistence.
- Storage and formatting remain independent from context collection.
- Public APIs remain small while internal modules can evolve.
