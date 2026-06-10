# Usage

Vestigium is enabled once, near the application entry point.

```python
from vestigium import start

start(
    project_name="my-application",
    reports_directory=".reports",
    capture_locals=True,
)
```

After `start()` is called, uncaught exceptions in the main process are
passed through the Vestigium handler.

## Generated files

Every captured exception creates two files with the same error identifier:

```text
.reports/
├── err-20260608-120000-ab12cd34.json
└── err-20260608-120000-ab12cd34.txt
```

The JSON file is intended for machines, automation, and future AI
integrations. The text file is intended for developers.

Report text is sanitized before either file is written. Sensitive local
variable names are fully redacted, and exception messages, traceback
source lines, and rendered local values are cleaned with LogPrivacy to
mask content such as emails, tokens, URLs, and card-like values.

## Disabling local variable capture

```python
from vestigium import start

start(
    project_name="my-application",
    capture_locals=False,
)
```

## Restoring the previous exception handler

```python
from vestigium import stop

stop()
```

## Important limitation

Exceptions caught by the application are not uncaught exceptions:

```python
try:
    dangerous_operation()
except Exception:
    pass
```

Vestigium does not automatically record this example because the program
handled the exception itself.
