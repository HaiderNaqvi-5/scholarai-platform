# Single-stage Dockerfile.
# DO App Platform's builder OOM'd on the prior 2-stage variant because
# `pip wheel ... --wheel-dir /app/wheels` cached ~2GB of compiled wheels
# (torch via sentence-transformers, lxml, shap, xgboost, pandas) and then
# stage 2 reinstalled them — doubling disk pressure past the builder cap.
# Single-stage skips the wheel-cache duplication.
#
# Capture path: Firecrawl Cloud (see services/ingestion/firecrawl_capture.py).
# Playwright + Chromium were removed in the C1-SSRF / Firecrawl swap because
# Firecrawl runs scraping from its own cloud — keeping a ~1.5 GB browser
# image in our worker just to fall back to was net negative for ops.
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PREFER_BINARY=1

# libpq-dev for asyncpg/psycopg2; build-essential for shap (no cp312 wheel, compiles from source).
# tini gives proper PID 1 signal handling for the celery worker / beat / uvicorn processes.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Install deps first for layer cache (changes less than source).
# Pre-install CPU-only PyTorch so sentence-transformers does not pull CUDA variant (~2GB saved).
# No GPU passthrough in compose; CPU inference is what runs at runtime.
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && (pip install --no-cache-dir --default-timeout=600 --retries 10 \
        --only-binary=:all: -r requirements.txt \
        || pip install --no-cache-dir --default-timeout=600 --retries 10 \
           -r requirements.txt)

COPY . .

# Run as non-root.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser /app
USER appuser

EXPOSE 8000

# Image is process-agnostic (same image runs uvicorn, celery worker, celery beat).
# Healthchecks live at the orchestration layer (DO app spec / docker-compose.yml).

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
