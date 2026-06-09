# Vestigium

Vestigium is a small Python library that records the context of uncaught
exceptions.

Its goal is to make failures easier to understand by creating structured
reports that can be read by developers and, in the future, by AI tools.

## What Vestigium captures

When an uncaught exception happens, Vestigium records:

- the exception type and message;
- the traceback frames;
- the source line related to each frame;
- local variables from the failing frame;
- basic runtime information;
- a unique identifier for the error.

Sensitive values such as passwords, tokens, cookies, API keys, and card
numbers are redacted before the report is written.

## Project structure

```text
vestigium/
├── .github/
│   └── workflows/
│       └── quality.yml
├── docs/
│   ├── architecture.md
│   ├── development.md
│   └── usage.md
├── examples/
│   └── basic_error.py
├── src/
│   ├── core/
│   ├── integrations/
│   ├── models/
│   ├── reports/
│   ├── storage/
│   └── utils/
├── tests/
├── pyproject.toml
└── requirements-dev.txt
```

## Quick start

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the example:

```bash
python examples/basic_error.py
```

The example intentionally raises an exception. Vestigium creates JSON and
text reports inside:

```text
.reports/
```

## Basic usage

```python
from src import start

start(project_name="my-application")
```

Vestigium can be disabled and the previous Python exception handler
restored:

```python
from src import stop

stop()
```

## Quality checks

```bash
ruff check .
ruff format --check .
mypy src
pytest --cov=src --cov-report=term-missing
```

## Documentation

- [Usage](docs/usage.md)
- [Architecture](docs/architecture.md)
- [Development](docs/development.md)

## Current limitations

This is an early version. It currently captures uncaught exceptions from
the main Python process only.

It does not yet support:

- automatic replay;
- thread exception handlers;
- async task integrations;
- Django, Flask, FastAPI, or pytest plugins;
- remote report storage;
- automatic AI analysis.
