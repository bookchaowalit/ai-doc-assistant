"""Demo mode: the same upload/retrieve/cite flow with no AI provider.

Embeddings are a local hashed bag of words plus character trigrams (so Thai text, which has
no spaces, still matches), and the "answer" is the best-matching passage quoted verbatim.
Nothing here imports or calls OpenAI, and the demo index is separate from the live one, so
anonymous uploads never reach live users and cost nothing.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import TYPE_CHECKING

from rag_engine import RAGEngine

if TYPE_CHECKING:
    from openai import OpenAI

DEMO_DIMENSIONS = 512
DEMO_MAX_CHUNKS = 2000
DEMO_PREFIX = "[Demo mode: no AI model was called. Best-matching passage from the uploaded documents]"
_WORD = re.compile(r"\w+", re.UNICODE)


def _features(text: str) -> list[str]:
    features: list[str] = []
    for word in _WORD.findall(text.lower()):
        features.append(f"w:{word}")
        padded = f" {word} "
        features.extend(f"c:{padded[i : i + 3]}" for i in range(len(padded) - 2))
    return features


def hashed_embedding(text: str, dimensions: int = DEMO_DIMENSIONS) -> list[float]:
    """Deterministic, L2-normalised feature-hashing vector (not a semantic model)."""
    vector = [0.0] * dimensions
    for feature in _features(text):
        digest = hashlib.blake2b(feature.encode(), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        vector[0] = 1.0
        return vector
    return [v / norm for v in vector]


class DemoKnowledgeBaseFull(Exception):
    """The in-memory demo index reached DEMO_MAX_CHUNKS."""


class DemoRAGEngine(RAGEngine):
    collection_name = "demo_knowledge_base"
    # Lexical vectors are far apart for paraphrases; this cut-off was tuned on the bundled samples.
    no_evidence_distance = 0.85

    def __init__(self) -> None:
        super().__init__()
        self._api_key = ""

    @property
    def client(self) -> OpenAI:
        raise RuntimeError("Demo mode never calls an AI provider.")

    def _embed(self, texts: list[str]) -> tuple[list[list[float]], int]:
        return [hashed_embedding(t) for t in texts], 0

    def ingest_chunks(self, chunks: list[dict]) -> None:
        if self.total_chunks + len(chunks) > DEMO_MAX_CHUNKS:
            raise DemoKnowledgeBaseFull
        super().ingest_chunks(chunks)

    def _generate_answer(self, question: str, context: str) -> tuple[str, float]:
        best = context.split("\n\n", 1)[0].strip()
        if len(best) > 600:
            best = best[:600].rstrip() + "..."
        return f"{DEMO_PREFIX}\n\n{best}", 0.0
