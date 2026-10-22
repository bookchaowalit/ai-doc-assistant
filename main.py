"""
RAG-as-a-Service Demo — FastAPI Backend
Turn company documents into an AI assistant that answers questions 24/7
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from access import AccessMode, access_mode
from demo_engine import DemoKnowledgeBaseFull, DemoRAGEngine
from document_processor import DocumentProcessor
from limits import MemoryCounterStore, check_limits
from observability import init_sentry
from rag_engine import RAGEngine

load_dotenv()
init_sentry()

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
cors_origins = [
    origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8000").split(",") if origin.strip()
]

app = FastAPI(
    title="RAG-as-a-Service",
    description="Turn company documents into an AI assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines. `rag_engine` (OpenAI) serves only token holders; `demo_engine` serves
# everyone else from a separate local index and never calls a provider (see access.py).
doc_processor = DocumentProcessor()
rag_engine = RAGEngine()
demo_engine = DemoRAGEngine()
limit_store = MemoryCounterStore()


def reset_runtime_state() -> None:
    """Clear rate-limit counters and the demo index (used by tests)."""
    global limit_store
    limit_store = MemoryCounterStore()
    demo_engine.reset()


def _client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _admit(request: Request, authorization: str | None) -> tuple[AccessMode, RAGEngine]:
    """Resolve the caller's mode and enforce the rate limit and daily cap before any work."""
    mode = access_mode(authorization)
    decision = check_limits(limit_store, _client_id(request), mode, os.environ, time.time())
    if not decision.ok:
        headers = {"Retry-After": str(decision.retry_after)} if decision.retry_after else None
        raise HTTPException(status_code=decision.status, detail=decision.detail, headers=headers)
    return mode, (rag_engine if mode == "live" else demo_engine)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float
    latency_ms: float
    cost_usd: float
    grounded: bool
    mode: str


# Serve static files (chat UI)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
async def health():
    """Liveness: process is up and event loop is responsive."""
    return {"status": "ok"}


@app.get("/healthz")
async def healthz():
    """Kubernetes-style liveness alias."""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    """
    Readiness: process accepts traffic.
    Does not require OpenAI connectivity (query endpoints fail closed without a key).
    """
    return {"status": "ready"}


@app.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008 - FastAPI dependency marker, evaluated by FastAPI per request
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Upload and process a document"""
    mode, engine = _admit(request, authorization)
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Filename must be a single safe name")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported document type")

    temp_path = None
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Document exceeds the upload size limit")

        with tempfile.NamedTemporaryFile(mode="wb", prefix="ai-doc-", suffix=extension, delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        # Process document
        result = doc_processor.process(temp_path, filename)

        # Generate embeddings and store
        try:
            engine.ingest_chunks(result["chunks"])
        except DemoKnowledgeBaseFull as exc:
            raise HTTPException(status_code=507, detail="The demo knowledge base is full. Try again later.") from exc
        except RuntimeError as exc:
            if "OPENAI_API_KEY is not set" in str(exc):
                raise HTTPException(
                    status_code=503,
                    detail="AI provider is not configured for document ingestion",
                ) from exc
            raise

        return {
            "status": "success",
            "mode": mode,
            "filename": filename,
            "chunks_created": len(result["chunks"]),
            "message": f"Document processed into {len(result['chunks'])} chunks",
        }
    except HTTPException:
        raise
    except (UnicodeDecodeError, ValueError) as exc:
        logger.warning("Rejected document %s: %s", filename, exc)
        raise HTTPException(status_code=422, detail="Document could not be processed") from exc
    except Exception as e:
        logger.exception("Document processing failed for %s", filename)
        raise HTTPException(status_code=500, detail="Document processing failed") from e
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    body: QueryRequest,
    request: Request,
    authorization: str | None = Header(default=None),
) -> QueryResponse:
    """Ask a question and get an answer with citations"""
    mode, engine = _admit(request, authorization)
    try:
        result = engine.query(body.question, top_k=body.top_k)
        return QueryResponse(**result, mode=mode)
    except RuntimeError as exc:
        if "OPENAI_API_KEY is not set" in str(exc):
            raise HTTPException(
                status_code=503,
                detail="AI provider is not configured for querying",
            ) from exc
        logger.exception("Query runtime failure")
        raise HTTPException(status_code=500, detail="Query could not be completed") from exc
    except Exception as exc:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail="Query could not be completed") from exc


@app.get("/stats")
async def get_stats(authorization: str | None = Header(default=None)) -> dict[str, object]:
    """Knowledge base statistics for the caller's mode (no provider call, not rate-limited)."""
    mode = access_mode(authorization)
    stats = (rag_engine if mode == "live" else demo_engine).get_stats()
    return {**stats, "mode": mode}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
