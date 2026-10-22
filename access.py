"""Access gate: who may spend the OpenAI key.

Callers that present ``DOC_ASSISTANT_ACCESS_TOKEN`` as ``Authorization: Bearer <token>``
get live mode (OpenAI embeddings + chat). Everyone else gets demo mode, which uses a local
index and never calls a provider. A missing or too-short server token fails closed: nobody
gets live mode until the operator sets a real secret.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from collections.abc import Mapping
from typing import Literal

MIN_TOKEN_CHARS = 24
TOKEN_ENV = "DOC_ASSISTANT_ACCESS_TOKEN"

AccessMode = Literal["live", "demo"]

_BEARER = re.compile(r"^Bearer\s+(\S+)\s*$", re.IGNORECASE)


def configured_token(env: Mapping[str, str]) -> str | None:
    token = env.get(TOKEN_ENV, "").strip()
    return token if len(token) >= MIN_TOKEN_CHARS else None


def presented_token(authorization: str | None) -> str | None:
    match = _BEARER.match(authorization or "")
    return match.group(1) if match else None


def _same_secret(a: str, b: str) -> bool:
    """Compare digests so the check takes the same time whatever the input length."""
    return hmac.compare_digest(hashlib.sha256(a.encode()).digest(), hashlib.sha256(b.encode()).digest())


def access_mode(authorization: str | None, env: Mapping[str, str] | None = None) -> AccessMode:
    expected = configured_token(os.environ if env is None else env)
    presented = presented_token(authorization)
    if expected is None or presented is None:
        return "demo"
    return "live" if _same_secret(presented, expected) else "demo"
