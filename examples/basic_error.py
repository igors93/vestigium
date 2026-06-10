import sys
from pathlib import Path

# Make the local package available without installing the project.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from vestigium import start

start(project_name="sample-store")


def calculate_total(price: str, discount: int) -> int:
    password = "this-value-must-not-appear"  # noqa: F841
    return price - discount  # type: ignore[operator]


calculate_total("100", 10)
