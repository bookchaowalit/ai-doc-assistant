"""Demo engine: local retrieval with citations, and provably no provider call."""

import os
import unittest
from unittest.mock import patch

with patch.dict(os.environ, {"ANONYMIZED_TELEMETRY": "False"}):
    import demo_engine
    from demo_engine import DEMO_PREFIX, DemoKnowledgeBaseFull, DemoRAGEngine, hashed_embedding
    from document_processor import DocumentProcessor
    from rag_engine import NOT_FOUND_MESSAGE

SAMPLES = os.path.join(os.path.dirname(__file__), "sample-documents")


class DemoEngineTests(unittest.TestCase):
    engine: DemoRAGEngine

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = DemoRAGEngine()
        processor = DocumentProcessor()
        for name in ("company-policy.txt", "thai-legal-contract.txt"):
            cls.engine.ingest_chunks(processor.process(os.path.join(SAMPLES, name), name)["chunks"])

    def test_embedding_is_deterministic_and_normalised(self) -> None:
        a = hashed_embedding("วันลาพักร้อน annual leave")
        self.assertEqual(a, hashed_embedding("วันลาพักร้อน annual leave"))
        self.assertAlmostEqual(sum(v * v for v in a), 1.0, places=6)
        self.assertAlmostEqual(sum(v * v for v in hashed_embedding("")), 1.0, places=6)

    def test_thai_question_is_answered_from_the_right_document_at_zero_cost(self) -> None:
        with patch("rag_engine.OpenAI", side_effect=AssertionError("provider must not be called")):
            result = self.engine.query("วันลาพักร้อนกี่วัน")
        self.assertTrue(result["grounded"])
        self.assertTrue(result["answer"].startswith(DEMO_PREFIX))
        self.assertEqual(result["sources"][0]["source"], "company-policy.txt")
        self.assertEqual(result["cost_usd"], 0)

    def test_unrelated_question_is_not_found(self) -> None:
        result = self.engine.query("How do I bake sourdough bread at home?")
        self.assertFalse(result["grounded"])
        self.assertEqual(result["answer"], NOT_FOUND_MESSAGE)
        self.assertEqual(result["sources"], [])

    def test_demo_client_refuses_provider_access(self) -> None:
        with self.assertRaises(RuntimeError):
            _ = self.engine.client

    def test_demo_index_is_bounded(self) -> None:
        engine = DemoRAGEngine()
        chunk = {"id": "x-0", "text": "t", "metadata": {"source": "x", "chunk_id": 0}}
        with patch.object(demo_engine, "DEMO_MAX_CHUNKS", 0), self.assertRaises(DemoKnowledgeBaseFull):
            engine.ingest_chunks([chunk])
        self.assertEqual(engine.total_chunks, 0)


if __name__ == "__main__":
    unittest.main()
