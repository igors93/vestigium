# Development

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

`requirements-dev.txt` points to the same editable install.

## Run All Checks

```bash
ruff check .
ruff format --check .
mypy src/vestigium
pytest --cov=vestigium --cov-report=term-missing
```

## Apply Safe Ruff Fixes

```bash
ruff check . --fix
ruff format .
```

## Test Organization

- `test_api.py`: public API and compatibility wrappers;
- `test_config.py`: configuration limits;
- `test_context.py`: context nesting, cleanup, event buffers, isolation;
- `test_handler.py`: exception capture and defensive behavior;
- `test_integration.py`: subprocess workflow with uncaught exception;
- `test_reports.py`: optional text rendering;
- `test_sanitizer.py`: privacy adapter behavior;
- `test_snapshots.py`: reproduction facts and limitations;
- `test_storage.py`: JSON store and persistence boundary.

## Commit Guidance

Keep commits focused around behavior:

```text
feat: add forensic snapshot model
feat: add context and event capture
feat: add anomaly and exception incidents
docs: describe forensic diagnostics workflow
```
