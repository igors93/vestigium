from vestigium import configure, context, event

configure(project_name="sample-store")


def calculate_total(price: str, discount: int) -> int:
    password = "this-value-must-not-appear"  # noqa: F841
    return price - discount  # type: ignore[operator]


with context("calculate_total", order_id="ord-123"):
    event("calculation_started")
    calculate_total("100", 10)
