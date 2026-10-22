FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application (exclude local .venv via .dockerignore when present)
COPY main.py access.py limits.py demo_engine.py observability.py document_processor.py rag_engine.py requirements.txt ./
COPY static ./static
COPY sample-documents ./sample-documents

# Writable runtime paths for non-root
RUN mkdir -p /app/chroma-data /app/uploads /tmp \
    && useradd --create-home --uid 65532 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app /tmp

USER 65532:65532

EXPOSE 8000

# Container-level healthcheck (Kubernetes probes also use /health)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
