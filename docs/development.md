# Development

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Run all checks

```bash
ruff check .
ruff format --check .
mypy src/vestigium
pytest --cov=vestigium --cov-report=term-missing
```

## Apply safe Ruff fixes

```bash
ruff check . --fix
ruff format .
```

## Test organization

- `test_api.py`: public start and stop functions;
- `test_config.py`: configuration behavior;
- `test_context.py`: exception context collection;
- `test_handler.py`: global exception handler behavior;
- `test_integration.py`: complete subprocess workflow;
- `test_reports.py`: text report generation;
- `test_sanitizer.py`: sensitive data handling;
- `test_storage.py`: JSON persistence.

## Intentional unused variables

Some tests and examples create local variables only so Vestigium can capture
them. These lines use `# noqa: F841` because the unused assignment is
intentional and part of the behavior being tested.

## Suggested commit order

Keep changes focused:

```text
test: expand error capture coverage
fix: improve sensitive value redaction
docs: add project documentation
chore: configure quality checks
```
