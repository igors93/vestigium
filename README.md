# Vestigium

Vestigium is a small error recorder for Python applications.

It captures uncaught exceptions and creates:

- a JSON report for structured data;
- a text report for human reading;
- a unique identifier for every captured error.

## Structure

```text
vestigium/
├── .github/workflows/
├── src/
├── examples/
├── tests/
├── pyproject.toml
└── requirements-dev.txt
```

## Run the example

From the project root:

```bash
python examples/basic_error.py
```

Reports are written to:

```text
.reports/
```

## Development

Install the development tools:

```bash
python -m pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

Check and format the code:

```bash
ruff check .
ruff format --check .
```

Run the type checker:

```bash
mypy src
```

## Current scope

- Captures uncaught exceptions in the main Python process.
- Records traceback frames.
- Captures local variables from the failing frame.
- Redacts common sensitive values.
- Creates JSON and plain-text reports.
- Restores the previous exception handler with `stop()`.

Automatic replay and framework integrations are planned for later versions.
