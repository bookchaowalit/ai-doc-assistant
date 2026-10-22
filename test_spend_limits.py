"""Rate limit and daily spend cap: provider calls are bounded and fail closed."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

with (
    patch("dotenv.load_dotenv"),
    patch.dict(os.environ, {"OPENAI_API_KEY": "", "ANONYMIZED_TELEMETRY": "False"}),
):
    import main
    from limits import DAY_SECONDS, MemoryCounterStore, parse_positive_int

TOKEN = "s" * 32
AUTH = {"Authorization": f"Bearer {TOKEN}"}
LIVE_RESULT = {
    "answer": "live",
    "sources": [],
    "confidence": 0.5,
    "latency_ms": 1,
    "cost_usd": 0.0,
    "grounded": False,
}


class SpendLimitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = {
            "OPENAI_API_KEY": "synthetic-not-a-real-key",
            "DOC_ASSISTANT_ACCESS_TOKEN": TOKEN,
            "DOC_ASSISTANT_DAILY_REQUEST_CAP": "3",
            "DOC_ASSISTANT_RATE_LIMIT_PER_MINUTE": "2",
            "DOC_ASSISTANT_DEMO_RATE_LIMIT_PER_MINUTE": "2",
        }
        env = patch.dict(os.environ, self.env)
        env.start()
        self.addCleanup(env.stop)
        main.reset_runtime_state()
        self.client = TestClient(main.app)
        live = patch.object(main.rag_engine, "query", return_value=LIVE_RESULT)
        self.live_query = live.start()
        self.addCleanup(live.stop)

    def _ask(self, headers: dict[str, str] | None = None):
        return self.client.post("/query", json={"question": "q"}, headers=headers or {})

    def test_per_client_rate_limit_returns_429_with_retry_after(self) -> None:
        self.assertEqual(self._ask(AUTH).status_code, 200)
        self.assertEqual(self._ask(AUTH).status_code, 200)
        blocked = self._ask(AUTH)
        self.assertEqual(blocked.status_code, 429)
        self.assertGreaterEqual(int(blocked.headers["Retry-After"]), 1)
        self.assertEqual(self.live_query.call_count, 2)

    def test_demo_traffic_is_rate_limited_too(self) -> None:
        self._ask()
        self._ask()
        self.assertEqual(self._ask().status_code, 429)
        self.live_query.assert_not_called()

    def test_daily_cap_stops_provider_calls_for_everyone(self) -> None:
        with patch.dict(os.environ, {"DOC_ASSISTANT_RATE_LIMIT_PER_MINUTE": "100"}):
            for _ in range(3):
                self.assertEqual(self._ask(AUTH).status_code, 200)
            capped = self._ask(AUTH)
        self.assertEqual(capped.status_code, 429)
        self.assertIn("daily", capped.json()["detail"].lower())
        self.assertEqual(self.live_query.call_count, 3)

    def test_misconfigured_cap_fails_closed(self) -> None:
        for bad in ("abc", "0", "-5", "1.5"):
            with self.subTest(cap=bad), patch.dict(os.environ, {"DOC_ASSISTANT_DAILY_REQUEST_CAP": bad}):
                main.reset_runtime_state()
                self.assertEqual(self._ask(AUTH).status_code, 503)
        self.live_query.assert_not_called()

    def test_live_upload_counts_against_the_daily_cap(self) -> None:
        with (
            patch.dict(os.environ, {"DOC_ASSISTANT_RATE_LIMIT_PER_MINUTE": "100", "DOC_ASSISTANT_DAILY_REQUEST_CAP": "1"}),
            patch.object(main.rag_engine, "ingest_chunks") as ingest,
        ):
            first = self.client.post("/upload", files={"file": ("a.txt", b"text", "text/plain")}, headers=AUTH)
            second = self.client.post("/upload", files={"file": ("b.txt", b"text", "text/plain")}, headers=AUTH)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(ingest.call_count, 1)


class CounterStoreTests(unittest.TestCase):
    def test_fixed_window_resets(self) -> None:
        store = MemoryCounterStore()
        self.assertEqual(store.increment("k", 60, now=0).count, 1)
        self.assertEqual(store.increment("k", 60, now=59).count, 2)
        fresh = store.increment("k", 60, now=60)
        self.assertEqual(fresh.count, 1)
        self.assertEqual(fresh.reset_at, 120)

    def test_daily_window_is_utc_day(self) -> None:
        store = MemoryCounterStore()
        self.assertEqual(store.increment("d", DAY_SECONDS, now=DAY_SECONDS - 1).reset_at, DAY_SECONDS)

    def test_key_table_is_bounded(self) -> None:
        store = MemoryCounterStore(max_keys=3)
        for i in range(10):
            store.increment(f"k{i}", 60, now=0)
        self.assertLessEqual(len(store), 3)

    def test_parse_positive_int(self) -> None:
        self.assertEqual(parse_positive_int(None, 7), 7)
        self.assertEqual(parse_positive_int(" ", 7), 7)
        self.assertEqual(parse_positive_int("12", 7), 12)
        for bad in ("0", "-1", "x", "1.5"):
            self.assertIsNone(parse_positive_int(bad, 7))


if __name__ == "__main__":
    unittest.main()
