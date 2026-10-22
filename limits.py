"""Per-client rate limit and a deployment-wide daily cap on provider-backed requests.

Counters are in process memory (one instance, best-effort; they reset on restart). The daily
cap (``DOC_ASSISTANT_DAILY_REQUEST_CAP``, default 200 per UTC day) counts every live upload
and query, which bounds OpenAI spend. It fails closed: a misconfigured value stops live
requests instead of lifting the limit. Demo traffic never calls a provider, so it is only
rate-limited per client.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass

DAY_SECONDS = 24 * 60 * 60
MINUTE_SECONDS = 60

DEFAULT_DAILY_CAP = 200
DEFAULT_LIVE_PER_MINUTE = 10
DEFAULT_DEMO_PER_MINUTE = 30


@dataclass(frozen=True)
class WindowCount:
    count: int
    reset_at: int  # epoch seconds when this window ends


class MemoryCounterStore:
    """Fixed-window counters with a bounded key table."""

    def __init__(self, max_keys: int = 5000) -> None:
        self._counts: dict[str, WindowCount] = {}
        self._max_keys = max_keys
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._counts)

    def increment(self, key: str, window_seconds: int, now: float) -> WindowCount:
        index = int(now // window_seconds)
        reset_at = (index + 1) * window_seconds
        slot = f"{key}:{window_seconds}:{index}"
        with self._lock:
            entry = self._counts.get(slot)
            if entry is None:
                if len(self._counts) >= self._max_keys:
                    for k in [k for k, v in self._counts.items() if v.reset_at <= now]:
                        del self._counts[k]
                    if len(self._counts) >= self._max_keys:
                        self._counts.clear()
                entry = WindowCount(0, reset_at)
            entry = WindowCount(entry.count + 1, entry.reset_at)
            self._counts[slot] = entry
            return entry


def parse_positive_int(value: str | None, default: int) -> int | None:
    """Positive integer from env, ``default`` when unset/blank, ``None`` when invalid."""
    if value is None or not value.strip():
        return default
    text = value.strip()
    if not text.isdigit():
        return None
    number = int(text)
    return number if number > 0 else None


@dataclass(frozen=True)
class Decision:
    ok: bool
    status: int = 200
    detail: str = ""
    retry_after: int | None = None


def _retry_after(reset_at: int, now: float) -> int:
    return max(1, int(reset_at - now + 0.999))


def check_limits(
    store: MemoryCounterStore,
    client: str,
    mode: str,
    env: Mapping[str, str],
    now: float,
) -> Decision:
    if mode == "live":
        per_minute = parse_positive_int(env.get("DOC_ASSISTANT_RATE_LIMIT_PER_MINUTE"), DEFAULT_LIVE_PER_MINUTE)
        daily_cap = parse_positive_int(env.get("DOC_ASSISTANT_DAILY_REQUEST_CAP"), DEFAULT_DAILY_CAP)
        if per_minute is None or daily_cap is None:
            return Decision(False, 503, "AI requests are paused: the request limits are misconfigured.")
    else:
        per_minute = parse_positive_int(env.get("DOC_ASSISTANT_DEMO_RATE_LIMIT_PER_MINUTE"), DEFAULT_DEMO_PER_MINUTE)
        daily_cap = None
        if per_minute is None:
            return Decision(False, 503, "Demo requests are paused: the rate limit is misconfigured.")

    window = store.increment(f"{mode}:client:{client}", MINUTE_SECONDS, now)
    if window.count > per_minute:
        return Decision(
            False, 429, "Too many requests. Wait a minute and try again.", _retry_after(window.reset_at, now)
        )
    if daily_cap is not None:
        daily = store.increment("live:daily", DAY_SECONDS, now)
        if daily.count > daily_cap:
            return Decision(
                False,
                429,
                "The daily AI request budget is used up. Try again tomorrow (UTC).",
                _retry_after(daily.reset_at, now),
            )
    return Decision(True)
