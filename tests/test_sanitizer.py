import pytest
from src.core.sanitizer import safe_repr, sanitize_mapping


class BrokenRepr:
    def __repr__(self) -> str:
        raise RuntimeError("cannot render")


def test_sensitive_values_are_redacted():
    result = sanitize_mapping(
        {
            "username": "alex",
            "password": "secret-value",
            "api_token": "token-value",
            "cardNumber": "1234",
        }
    )

    assert result["username"] == "'alex'"
    assert result["password"] == "<redacted>"
    assert result["api_token"] == "<redacted>"
    assert result["cardNumber"] == "<redacted>"


def test_normal_names_are_not_false_positives():
    result = sanitize_mapping(
        {
            "secretary_name": "Ana",
            "tokenizer": "basic",
        }
    )

    assert result["secretary_name"] == "'Ana'"
    assert result["tokenizer"] == "'basic'"


def test_long_values_are_truncated():
    rendered = safe_repr("x" * 100, max_length=10)

    assert rendered.endswith("...<truncated>")


def test_broken_repr_does_not_break_capture():
    rendered = safe_repr(BrokenRepr())

    assert rendered == "<BrokenRepr: unavailable>"


def test_negative_max_length_is_rejected():
    with pytest.raises(ValueError, match="zero or greater"):
        safe_repr("value", max_length=-1)
