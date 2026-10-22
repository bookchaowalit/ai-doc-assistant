"""Open-relay regression: only callers holding the access token may spend the provider key.

Everyone else gets demo mode, which answers from a local index and never calls a provider.
All tests are offline: the live engine is mocked, no OpenAI request is made.
"""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

with (
    patch("dotenv.load_dotenv"),
    patch.dict(os.environ, {"OPENAI_API_KEY": "", "ANONYMIZED_TELEMETRY": "False"}),
):
    import main

TOKEN = "t" * 32
LIVE_RESULT = {
    "answer": "live answer",
    "sources": [{"source": "fixture.txt", "chunk_id": 0}],
    "confidence": 0.9,
    "latency_ms": 1,
    "cost_usd": 0.001,
    "grounded": True,
}


class AccessGateTests(unittest.TestCase):
    def setUp(self) -> None:
        env = patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "synthetic-not-a-real-key",
                "DOC_ASSISTANT_ACCESS_TOKEN": TOKEN,
                "DOC_ASSISTANT_DAILY_REQUEST_CAP": "100",
                "DOC_ASSISTANT_RATE_LIMIT_PER_MINUTE": "100",
            },
        )
        env.start()
        self.addCleanup(env.stop)
        main.reset_runtime_state()
        self.client = TestClient(main.app)
        live_query = patch.object(main.rag_engine, "query", return_value=LIVE_RESULT)
        live_ingest = patch.object(main.rag_engine, "ingest_chunks")
        self.live_query = live_query.start()
        self.live_ingest = live_ingest.start()
        self.addCleanup(live_query.stop)
        self.addCleanup(live_ingest.stop)

    def _query(self, headers: dict[str, str] | None = None):
        return self.client.post("/query", json={"question": "refund policy"}, headers=headers or {})

    def test_anonymous_query_never_reaches_the_provider(self) -> None:
        response = self._query()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "demo")
        self.assertEqual(response.json()["cost_usd"], 0)
        self.live_query.assert_not_called()

    def test_wrong_or_malformed_token_gets_demo(self) -> None:
        for header in (f"Bearer {'x' * 32}", TOKEN, f"Basic {TOKEN}", f"Bearer {TOKEN}extra"):
            with self.subTest(header=header):
                response = self._query({"Authorization": header})
                self.assertEqual(response.json()["mode"], "demo")
        self.live_query.assert_not_called()

    def test_valid_token_uses_live_engine(self) -> None:
        response = self._query({"Authorization": f"Bearer {TOKEN}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "live")
        self.assertEqual(response.json()["answer"], "live answer")
        self.live_query.assert_called_once()

    def test_unset_or_short_server_token_fails_closed(self) -> None:
        for configured in ("", "short-token"):
            with (
                self.subTest(configured=configured),
                patch.dict(os.environ, {"DOC_ASSISTANT_ACCESS_TOKEN": configured}),
            ):
                response = self._query({"Authorization": f"Bearer {configured}"})
                self.assertEqual(response.json()["mode"], "demo")
        self.live_query.assert_not_called()

    def test_anonymous_upload_is_indexed_locally_and_answerable_in_demo(self) -> None:
        upload = self.client.post(
            "/upload",
            files={"file": ("policy.txt", b"Refunds are paid within 14 days of a written request.", "text/plain")},
        )
        self.assertEqual(upload.status_code, 200)
        self.assertEqual(upload.json()["mode"], "demo")
        self.live_ingest.assert_not_called()

        answer = self.client.post("/query", json={"question": "How many days until refunds are paid?"})
        body = answer.json()
        self.assertEqual(body["mode"], "demo")
        self.assertTrue(body["grounded"])
        self.assertEqual(body["sources"][0]["source"], "policy.txt")
        self.assertIn("14 days", body["answer"])
        self.live_query.assert_not_called()

    def test_stats_follow_the_callers_mode(self) -> None:
        self.client.post("/upload", files={"file": ("a.txt", b"demo document text", "text/plain")})
        self.assertEqual(self.client.get("/stats").json()["total_documents"], 1)
        live = self.client.get("/stats", headers={"Authorization": f"Bearer {TOKEN}"}).json()
        self.assertEqual(live["total_documents"], main.rag_engine.total_documents)


if __name__ == "__main__":
    unittest.main()
