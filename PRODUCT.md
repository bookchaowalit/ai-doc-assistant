# ai-doc-assistant: product sheet

Describes only what exists today (2026-10-22).

## Purpose

A demo of retrieval-augmented question answering over uploaded company documents: upload
PDF/DOCX/TXT files, ask a question in Thai or English, get an answer that cites the source chunks,
or an explicit "not found" when nothing relevant was retrieved.

## Users

The owner, as a portfolio/lab demo and a starting point for client conversations. There are no
external users and no tenants.

## What works

- FastAPI app with a single-page chat UI at `/`, `/upload`, `/query`, `/stats`, and health probes
  `/health`, `/healthz`, `/readyz`.
- Upload bounds: allowed types, a safe single filename, 10 MiB limit, temp file always removed.
- Chunking (500 characters, 50 overlap) and in-memory ChromaDB retrieval with a no-evidence cut-off.
- Access gate, per-client rate limit, daily cap on provider-backed requests, and a provider-free
  demo mode (see "AI").
- Prompt boundary: the question and retrieved text are delimited and marked as untrusted data.
- Opt-in Sentry error reporting (`SENTRY_DSN`), error events only, allowlist scrubber.
- CI: shared `platform-ci-workflows` v1.1.1 (ruff, mypy, offline pytest with a coverage gate, and the
  security workflow).

## How to run

See `README.md` ("Quick Start"). With no variables set the app runs in demo mode only.

## AI

- **Provider and models (live mode):** OpenAI, `text-embedding-3-small` for embeddings and `gpt-4o`
  (temperature 0.3, max 500 output tokens) for answers. Model ids are constants in `rag_engine.py`.
- **Who can spend the key:** only callers that send `Authorization: Bearer <DOC_ASSISTANT_ACCESS_TOKEN>`
  (the server token must be at least 24 characters; compared in constant time). Everyone else, and
  everyone when the token is unset or short, gets demo mode.
- **Spend bounds:** live requests are limited per client IP (default 10/minute) and per instance per
  UTC day (default 200 uploads + queries). Invalid limit values stop live requests (fail closed).
  The per-query cost shown is an estimate from list prices, not billing data.
- **Demo mode / fallback:** no provider call. A local hashed-keyword index (separate from the live
  one) returns the best-matching passage verbatim with its citation, cost 0. When live mode is
  requested but `OPENAI_API_KEY` is unset, `/upload` and `/query` return 503; there is no automatic
  fallback from live to demo.
- **Keys:** read from the environment only, never logged; no key-shaped string in the git history
  (checked 2026-10-22; only the `.env.example` placeholder).
- **Eval status:** gap: there is no eval set and no answer-quality threshold. Tests check the
  gate, limits, demo retrieval on the two bundled sample documents, contracts and the prompt
  boundary, with the provider mocked.

## Limits

- Everything is in process memory: documents, the index and rate-limit counters are lost on restart
  and are per instance.
- One shared live knowledge base: every token holder sees every live upload (no tenants, no
  per-user access control).
- Demo retrieval is lexical, not semantic: paraphrases often return "not found". Its cut-off was
  tuned on the two bundled samples only.
- The web UI sends no token, so in a browser the app is always in demo mode.
- Rate limiting keys on the connecting IP; behind a proxy all callers may share one bucket.

## Live URL

None. It has never been deployed (see `docs/delivery/STATUS-2026-08-11.md`). `railway.toml`,
`render.yaml` and the `Dockerfile` are deployment recipes, not running services.

## Disposition

Lab / demo. Tier and lifecycle in the ai-labs roadmap are still `unknown`; deciding between lab,
product or archive is an owner action.
