import unittest

from src.core.sanitizer import sanitize_mapping, safe_repr


class SanitizerTests(unittest.TestCase):
    def test_sensitive_values_are_redacted(self):
        result = sanitize_mapping(
            {
                "username": "alex",
                "password": "secret-value",
                "api_token": "token-value",
            }
        )

        self.assertEqual(result["username"], "'alex'")
        self.assertEqual(result["password"], "<redacted>")
        self.assertEqual(result["api_token"], "<redacted>")

    def test_long_values_are_truncated(self):
        rendered = safe_repr("x" * 100, max_length=10)
        self.assertTrue(rendered.endswith("...<truncated>"))


if __name__ == "__main__":
    unittest.main()
