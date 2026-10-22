# RAG-as-a-Service Demo

A demo FastAPI app: upload PDF/DOCX/TXT documents, then ask questions (Thai or English) and get
answers that cite the source chunks. Lab project: not deployed, no live URL. See `PRODUCT.md`
for what works today and its limits.

## Features

- **Document upload**: PDF, DOCX, TXT up to 10 MiB, chunked with overlap
- **Vector search**: ChromaDB, in process memory (lost on restart)
- **Two modes** (see "Access and spend control"):
  - **live**: OpenAI `text-embedding-3-small` + `gpt-4o` answers with citations, token holders only
  - **demo**: local hashed-keyword retrieval, quotes the best-matching passage, no AI provider call
- **No-evidence answer**: when nothing relevant is retrieved it says "not found" instead of guessing

## Quick Start

1. Install dependencies (Python 3.11):
```bash
uv sync --frozen --all-extras      # or: pip install -r requirements.txt
```

2. Run the server (demo mode works with no keys at all):
```bash
uv run uvicorn main:app --port 8000
```

3. For live mode, set the variables below in the shell or a local `.env` (never commit it).

## Access and spend control

The provider key is never spent for anonymous callers.

| Variable | Default | Meaning |
|---|---|---|
| `OPENAI_API_KEY` | unset | Needed for live mode only. Live requests without it return 503. |
| `DOC_ASSISTANT_ACCESS_TOKEN` | unset | Shared secret, at least 24 characters. Callers sending `Authorization: Bearer <token>` get live mode; everyone else gets demo mode. Unset or short = nobody gets live mode. |
| `DOC_ASSISTANT_RATE_LIMIT_PER_MINUTE` | 10 | Live requests per client IP per minute (429 + `Retry-After` above it). |
| `DOC_ASSISTANT_DEMO_RATE_LIMIT_PER_MINUTE` | 30 | Demo requests per client IP per minute. |
| `DOC_ASSISTANT_DAILY_REQUEST_CAP` | 200 | Live uploads + queries per UTC day for the whole instance. An invalid value stops live requests (503). |
| `SENTRY_DSN` | unset | Error reporting; off when unset. |
| `CORS_ALLOW_ORIGINS` | `http://localhost:8000` | Comma-separated allowed origins. |

Counters live in process memory: they reset on restart and are per instance. Demo uploads go to a
separate in-memory index (max 2000 chunks) and are never seen by live callers. The web UI at `/`
does not send a token, so it always runs in demo mode.

## API Endpoints

### Upload Document
```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer $DOC_ASSISTANT_ACCESS_TOKEN" \
  -F "file=@document.pdf"
```

### Query Knowledge Base
```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $DOC_ASSISTANT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?", "top_k": 3}'
```

Leave out the `Authorization` header to use demo mode.

### Get Stats
```bash
curl http://localhost:8000/stats
```

## Architecture

```
Client → FastAPI (access gate → rate limit / daily cap) → Document Processor → ChromaDB (in memory)
  live (token):  OpenAI embeddings → OpenAI gpt-4o answer with citations
  demo (no token): local hashed embeddings → best-matching passage quoted, no provider call
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Vector DB**: ChromaDB
- **LLM**: OpenAI GPT-4o
- **Embeddings**: OpenAI text-embedding-3-small
- **Document Parsing**: pypdf, python-docx

## Local checks

The same checks CI runs (offline; the provider is always mocked or unset):

```bash
uv sync --frozen --all-extras
uv run ruff check . && uv run ruff format --check .
uv run mypy .
uv run pytest -q --cov
```

The tests cover the access gate and demo mode (`test_access_gate.py`), rate limit and daily cap
(`test_spend_limits.py`), the demo engine (`test_demo_engine.py`), upload bounds
(`test_upload_safety.py`), API contracts (`test_api_contract.py`), the prompt/data boundary for
retrieved documents (`test_prompt_injection_boundary.py`) and the Sentry scrubber
(`test_observability.py`). They do not measure answer quality (no eval set yet).

The browser regression `test_ui_safety.cjs` serves the real HTML against synthetic responses and
needs Playwright with Chromium: `node test_ui_safety.cjs`. It is not run in CI.
