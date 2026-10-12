# RAG-as-a-Service Demo

Turn company documents into an AI assistant that answers questions 24/7 — in Thai, with citations.

## Features

- **Document Upload**: Upload PDF, DOCX, TXT files
- **Smart Chunking**: Automatic text segmentation with overlap
- **Vector Search**: ChromaDB for fast similarity search
- **AI Answers**: GPT-4o powered responses with source citations
- **Thai Language**: Full Thai NLP support

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

3. Run the server:
```bash
python main.py
```

4. Access the API:
- Swagger UI: http://localhost:8000/docs
- Upload documents: POST /upload
- Ask questions: POST /query

## API Endpoints

### Upload Document
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

### Query Knowledge Base
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?", "top_k": 3}'
```

### Get Stats
```bash
curl http://localhost:8000/stats
```

## Architecture

```
Client → FastAPI Backend → Document Processor → ChromaDB
                              ↓
                         OpenAI Embeddings
                              ↓
                         OpenAI GPT-4o
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Vector DB**: ChromaDB
- **LLM**: OpenAI GPT-4o
- **Embeddings**: OpenAI text-embedding-3-small
- **Document Parsing**: PyPDF2, python-docx

## Pricing Model

- **Setup Fee**: ฿30K-200K (one-time)
- **Monthly Retainer**: ฿5K-25K/month
- **ROI**: 1/10th the cost of hiring staff

## Target Customers

- Law firms (10-50 employees)
- Accounting firms
- Insurance companies
- Any document-heavy business

## Next Steps

- [x] Add web UI (Next.js chat interface) ✅ Inline HTML chat UI
- [x] Sample documents for demo ✅ Thai legal + HR docs
- [ ] Multi-tenant support
- [ ] Access control
- [ ] Analytics dashboard
- [ ] Deploy to Railway/Render

## Local regression checks

Run the bounded upload safety checks without a provider key:

```bash
.venv/bin/python -m unittest -v test_api_contract.py test_upload_safety.py test_prompt_injection_boundary.py
```

These checks cover unsupported types, traversal names, the 10 MiB size limit,
temporary-file cleanup, and the prompt/data boundary for retrieved documents.
They do not approve authentication, tenant isolation, provider-backed quality,
or deployment.

The API contract test disables dotenv loading and provider configuration before
importing the application. It covers query bounds, health/UI availability,
empty-collection behavior, missing-provider failure, and synthetic response
contracts. Run it first as shown above to keep the full suite provider-free.

The chat renders untrusted questions, answers, citation metadata, and errors as
text. Browser regressions also check duplicate submission and missing metrics.
With Playwright and Chromium already installed, run `node test_ui_safety.cjs`.
In the Solo Empire workspace, the existing dependency can be used from its root:

```bash
NODE_PATH="$PWD/infra/node_modules" node engagements/internal/solo-empire/ai-doc-assistant/test_ui_safety.cjs
```

This browser test serves the real HTML against synthetic loopback API responses,
blocks other origins, and shuts down after verification. It does not call a
model or establish production readiness.
