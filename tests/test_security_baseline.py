"""Security Baseline v1 tests (ETS-002.1 Commit A-3)."""

import re
import unittest
from pathlib import Path

from ui.broker.oauth_log import mask_oauth_url, sanitize_log_detail

ROOT = Path(__file__).resolve().parents[1]

_CREDENTIAL_PRINT_RE = re.compile(
    r"print\s*\([^)]*(api_secret|api_key|request_token|access_token|qp_token|ctx_token)",
    re.IGNORECASE,
)


class TestOAuthLogSanitization(unittest.TestCase):
    def test_sanitize_log_detail_redacts_request_token(self):
        raw = "callback http://localhost/?request_token=abc123secret&action=login"
        sanitized = sanitize_log_detail(raw)
        self.assertIn("request_token=***", sanitized)
        self.assertNotIn("abc123secret", sanitized)

    def test_sanitize_log_detail_redacts_api_secret(self):
        raw = "api_secret=supersecretvalue"
        self.assertIn("api_secret=***", sanitize_log_detail(raw))
        self.assertNotIn("supersecretvalue", sanitize_log_detail(raw))

    def test_mask_oauth_url_truncates_long_urls(self):
        url = "http://localhost/?request_token=" + ("x" * 200)
        masked = mask_oauth_url(url, max_len=80)
        self.assertLessEqual(len(masked), 81)
        self.assertIn("request_token=***", masked)


class TestBrokerOAuthSourceHygiene(unittest.TestCase):
    """Static checks — broker OAuth modules must not print credentials."""

    def test_kite_auth_has_no_credential_prints(self):
        source = (ROOT / "ui" / "components" / "kite_auth.py").read_text(encoding="utf-8")
        matches = _CREDENTIAL_PRINT_RE.findall(source)
        self.assertEqual(
            matches,
            [],
            f"credential print() calls found in kite_auth.py: {matches}",
        )

    def test_zerodha_exchange_has_no_session_data_print(self):
        source = (ROOT / "analyzer" / "zerodha.py").read_text(encoding="utf-8")
        self.assertNotIn('print("AFTER generate_session"', source)
        self.assertNotIn("print(\"BEFORE generate_session\"", source)

    def test_app_main_has_no_query_params_print(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("print(dict(st.query_params))", source)


if __name__ == "__main__":
    unittest.main()
