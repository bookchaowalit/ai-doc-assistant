"""Opt-in Sentry error reporting.

Off unless ``SENTRY_DSN`` is set and the ``sentry`` extra (sentry-sdk) is installed. Error
events only (no tracing), no default PII, and ``scrub_event`` keeps an allowlist of event
fields: request bodies, headers (Authorization, cookies), query strings, local variables and
user data are dropped, so uploaded documents, questions and tokens never leave the process.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

# Top-level event keys that may be sent. Everything else is removed.
ALLOWED_EVENT_KEYS = frozenset(
    {
        "event_id",
        "timestamp",
        "level",
        "logger",
        "platform",
        "environment",
        "release",
        "server_name",
        "exception",
        "message",
        "logentry",
        "tags",
        "sdk",
        "transaction",
        "fingerprint",
    }
)
# Request fields that may be sent (method and path only, no query, headers, body or cookies).
ALLOWED_REQUEST_KEYS = frozenset({"method", "url"})


def scrub_event(event: dict[str, Any], hint: object = None) -> dict[str, Any]:
    """Allowlist ``before_send`` hook: drop everything that could carry user data."""
    clean = {k: v for k, v in event.items() if k in ALLOWED_EVENT_KEYS}
    request = event.get("request")
    if isinstance(request, dict):
        kept = {k: v for k, v in request.items() if k in ALLOWED_REQUEST_KEYS}
        if isinstance(kept.get("url"), str):
            kept["url"] = kept["url"].split("?", 1)[0]
        clean["request"] = kept
    exception = clean.get("exception")
    if isinstance(exception, dict):
        for value in exception.get("values") or []:
            frames = (value.get("stacktrace") or {}).get("frames") or []
            for frame in frames:
                frame.pop("vars", None)
    return clean


def init_sentry() -> bool:
    """Initialise Sentry when ``SENTRY_DSN`` is set; return whether it is on."""
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        sdk = import_module("sentry_sdk")
    except ImportError:
        return False
    sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "local"),
        send_default_pii=False,
        include_local_variables=False,
        traces_sample_rate=0.0,
        before_send=scrub_event,
    )
    return True
