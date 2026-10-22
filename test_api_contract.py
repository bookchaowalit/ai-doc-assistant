"""Offline API contracts: disable dotenv and provider configuration before import."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

with (
    patch("dotenv.load_dotenv"),
    patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "",
            "ANONYMIZED_TELEMETRY": "False",
        },
    ),
):
    import main


TOKEN = "c" * 32
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class APIContractTests(unittest.TestCase):
    """Live-mode contract (token holder); the provider itself is always mocked or unset."""

    def setUp(self):
        env = patch.dict(os.environ, {"DOC_ASSISTANT_ACCESS_TOKEN": TOKEN})
        env.start()
        self.addCleanup(env.stop)
        main.reset_runtime_state()
        self.client = TestClient(main.app)

    def test_health_and_ui_do_not_require_provider(self):
        for route in ("/health", "/healthz", "/readyz"):
            self.assertEqual(self.client.get(route).status_code, 200)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="question"', response.text)

    def test_query_bounds_reject_before_engine(self):
        with patch.object(main.rag_engine, "query") as query:
            for payload in (
                {"question": ""},
                {"question": "x" * 2001},
                {"question": "synthetic", "top_k": 0},
                {"question": "synthetic", "top_k": 11},
            ):
                self.assertEqual(self.client.post("/query", json=payload).status_code, 422)
            query.assert_not_called()

    def test_provider_unconfigured_fails_closed(self):
        with (
            patch.object(main.rag_engine, "_api_key", ""),
            patch.object(main.rag_engine, "_client", None),
            patch.object(main.rag_engine, "total_chunks", 1),
        ):
            response = self.client.post("/query", json={"question": "synthetic question"}, headers=AUTH)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "AI provider is not configured for querying")

    def test_empty_collection_returns_no_evidence_without_provider(self):
        with (
            patch.object(main.rag_engine, "total_chunks", 0),
            patch.object(main.rag_engine, "_api_key", ""),
            patch.object(main.rag_engine, "_client", None),
        ):
            response = self.client.post("/query", json={"question": "synthetic question"}, headers=AUTH)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["grounded"])
        self.assertEqual(response.json()["cost_usd"], 0)

    def test_grounded_response_preserves_citation_contract(self):
        result = {
            "answer": "Synthetic answer",
            "sources": [{"source": "fixture.txt", "chunk_id": 0}],
            "confidence": 0.9,
            "latency_ms": 1,
            "cost_usd": 0,
            "grounded": True,
        }
        with patch.object(main.rag_engine, "query", return_value=result):
            response = self.client.post("/query", json={"question": "synthetic question"}, headers=AUTH)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {**result, "mode": "live"})

    def test_no_evidence_response_is_explicit(self):
        result = {
            "answer": "ไม่พบข้อมูลในเอกสาร",
            "sources": [],
            "confidence": 0,
            "latency_ms": 1,
            "cost_usd": 0,
            "grounded": False,
        }
        with patch.object(main.rag_engine, "query", return_value=result):
            response = self.client.post("/query", json={"question": "synthetic question"}, headers=AUTH)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["grounded"])
        self.assertEqual(response.json()["sources"], [])


if __name__ == "__main__":
    unittest.main()
