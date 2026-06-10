import pytest

from vestigium.core.sanitizer import safe_repr, sanitize_mapping, sanitize_text


class BrokenRepr:
    def __repr__(self) -> str:
        raise RuntimeError("cannot render")


def test_sensitive_values_are_redacted():
    result = sanitize_mapping(
        {
            "username": "alex",
            "password": "secret-value",
            "api_token": "token-value",
            "apikey": "key-value",
            "cardNumber": "1234",
        }
    )

    assert result["username"] == "'alex'"
    assert result["password"] == "<redacted>"
    assert result["api_token"] == "<redacted>"
    assert result["apikey"] == "<redacted>"
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


def test_sensitive_content_is_cleaned_in_regular_values():
    result = sanitize_mapping(
        {
            "message": "Login failed for ana@example.com with password=123456",
            "payment_reference": "4111111111111111",
        }
    )

    assert result["message"] == "'Login failed for [EMAIL] with password=[SECRET]'"
    assert result["payment_reference"] == "'[CREDIT_CARD]'"


def test_sensitive_text_is_cleaned():
    assert sanitize_text("User ana@example.com used password=123456") == (
        "User [EMAIL] used password=[SECRET]"
    )


def test_long_values_are_truncated():
    rendered = safe_repr("x" * 100, max_length=10)

    assert rendered.endswith("...<truncated>")


def test_broken_repr_does_not_break_capture():
    rendered = safe_repr(BrokenRepr())

    assert rendered == "<BrokenRepr: unavailable>"


def test_negative_max_length_is_rejected():
    with pytest.raises(ValueError, match="zero or greater"):
        safe_repr("value", max_length=-1)


def test_logprivacy_failure_does_not_return_uncleaned_value(monkeypatch):
    def fail_to_clean(*args, **kwargs):
        raise RuntimeError("cleaning failed")

    monkeypatch.setattr("vestigium.core.sanitizer.clean", fail_to_clean)

    assert safe_repr("email=ana@example.com") == "<redaction unavailable>"


def test_unexpected_logprivacy_result_is_converted_to_text(monkeypatch):
    def clean_to_number(*args, **kwargs):
        return 123

    monkeypatch.setattr("vestigium.core.sanitizer.clean", clean_to_number)

    assert safe_repr("value") == "123"
