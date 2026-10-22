"""Sentry stays off without a DSN, and the scrubber keeps only allowlisted fields."""

import os
import unittest
from unittest.mock import MagicMock, patch

import observability
from observability import init_sentry, scrub_event


class ScrubEventTests(unittest.TestCase):
    def test_drops_user_data_headers_body_and_locals(self) -> None:
        event = {
            "event_id": "e1",
            "level": "error",
            "user": {"ip_address": "203.0.113.9"},
            "extra": {"question": "secret contract text"},
            "breadcrumbs": {"values": [{"message": "uploaded salary.pdf"}]},
            "request": {
                "method": "POST",
                "url": "https://example.test/query?token=abc",
                "headers": {"Authorization": "Bearer t0ken"},
                "data": {"question": "private"},
                "cookies": "s=1",
            },
            "exception": {
                "values": [{"type": "ValueError", "stacktrace": {"frames": [{"function": "f", "vars": {"q": "x"}}]}}]
            },
        }
        clean = scrub_event(event)
        self.assertEqual(clean["event_id"], "e1")
        for dropped in ("user", "extra", "breadcrumbs"):
            self.assertNotIn(dropped, clean)
        self.assertEqual(clean["request"], {"method": "POST", "url": "https://example.test/query"})
        frame = clean["exception"]["values"][0]["stacktrace"]["frames"][0]
        self.assertNotIn("vars", frame)
        self.assertNotIn("t0ken", repr(clean))
        self.assertNotIn("private", repr(clean))


class InitSentryTests(unittest.TestCase):
    def test_off_without_dsn(self) -> None:
        with patch.dict(os.environ, {"SENTRY_DSN": ""}), patch.object(observability, "import_module") as imp:
            self.assertFalse(init_sentry())
        imp.assert_not_called()

    def test_on_with_dsn_uses_scrubber_and_no_pii(self) -> None:
        sdk = MagicMock()
        with (
            patch.dict(os.environ, {"SENTRY_DSN": "https://key@example.invalid/1"}),
            patch.object(observability, "import_module", return_value=sdk),
        ):
            self.assertTrue(init_sentry())
        kwargs = sdk.init.call_args.kwargs
        self.assertIs(kwargs["before_send"], scrub_event)
        self.assertFalse(kwargs["send_default_pii"])
        self.assertEqual(kwargs["traces_sample_rate"], 0.0)

    def test_off_when_sdk_missing(self) -> None:
        with (
            patch.dict(os.environ, {"SENTRY_DSN": "https://key@example.invalid/1"}),
            patch.object(observability, "import_module", side_effect=ImportError),
        ):
            self.assertFalse(init_sentry())


if __name__ == "__main__":
    unittest.main()
