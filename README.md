# Vestigium

Vestigium is a small error recorder for Python applications.

This initial version captures uncaught exceptions and creates:

- a JSON report for structured data;
- a text report for human reading;
- a unique identifier for every captured error.

## Structure

```text
vestigium/
├── README.md
├── .gitignore
├── src/
├── examples/
└── tests/
```

The `src` package contains all application source code.

## Run the example

Open a terminal inside the `vestigium` folder and run:

```bash
python examples/basic_error.py
```

Generated reports are stored in:

```text
.reports/
```

## Current scope

- Captures uncaught exceptions in the main Python process.
- Records traceback frames.
- Captures local variables from the failing frame.
- Redacts common sensitive values.
- Creates JSON and plain-text reports.
