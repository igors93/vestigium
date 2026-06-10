from __future__ import annotations

from vestigium.config import Config
from vestigium.privacy.adapter import safe_repr, sanitize_text, sanitize_value


class BrokenRepr:
    def __repr__(self) -> str:
        raise RuntimeError("cannot render")


def test_secret_in_sensitive_key_is_sanitized():
    sanitized = sanitize_value({"password": "secret-value"}, Config())

    assert sanitized.value == {"password": "[SECRET]"}


def test_secret_in_generic_value_is_sanitized():
    sanitized = sanitize_value(
        {"message": "Login failed for ana@example.com with password=123456"},
        Config(),
    )

    assert sanitized.value == {
        "message": "Login failed for [EMAIL] with password=[SECRET]"
    }


def test_nested_url_and_card_are_sanitized():
    sanitized = sanitize_value(
        {
            "payload": {
                "url": "https://example.test/callback?token=abc123456789",
                "card": "4111111111111111",
            }
        },
        Config(),
    )

    assert sanitized.value == {"payload": {"url": "[URL]", "card": "[CREDIT_CARD]"}}


def test_broken_repr_does_not_break_sanitization():
    sanitized = safe_repr(BrokenRepr(), Config())

    assert "BrokenRepr" in str(sanitized.value)
    assert "repr_unavailable" in sanitized.limitations


def test_recursive_structure_is_replaced_with_limitation():
    value: dict[str, object] = {}
    value["self"] = value

    sanitized = sanitize_value(value, Config())

    assert sanitized.value == {"self": "<recursion detected>"}
    assert "recursive_value_replaced" in sanitized.limitations


def test_large_value_is_truncated():
    sanitized = sanitize_text("x" * 100, Config(max_value_length=10))

    assert str(sanitized.value).endswith("...<truncated>")
    assert "value_truncated" in sanitized.limitations


def test_sanitizer_failure_returns_safe_marker(monkeypatch):
    def fail_to_clean(*args, **kwargs):
        raise RuntimeError("cleaning failed")

    monkeypatch.setattr("vestigium.privacy.adapter.clean", fail_to_clean)

    sanitized = sanitize_text("email=ana@example.com", Config())

    assert sanitized.value == "<redaction unavailable>"
    assert "privacy_sanitizer_failed" in sanitized.limitations
