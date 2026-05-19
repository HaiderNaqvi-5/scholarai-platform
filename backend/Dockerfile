# Single-stage Dockerfile.
# DO App Platform's builder OOM'd on the prior 2-stage variant because
# `pip wheel ... --wheel-dir /app/wheels` cached ~2GB of compiled wheels
# (torch via sentence-transformers, lxml, shap, xgboost, pandas) and then
# stage 2 reinstalled them — doubling disk pressure past the builder cap.
# Single-stage skips the wheel-cache duplication.
#
# Microsoft's Playwright Python image ships Chromium + all OS deps
# pre-installed at /ms-playwright pinned to the exact revision Playwright
# SDK 1.52.0 expects. Scraper Celery worker launches Chromium at runtime
# unchanged.
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PREFER_BINARY=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Only libpq-dev for asyncpg/psycopg2; jammy base has gcc/build-essential already.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install deps first for layer cache (changes less than source).
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=600 --retries 10 \
    --only-binary=:all: -r requirements.txt \
    || pip install --no-cache-dir --default-timeout=600 --retries 10 \
       -r requirements.txt

COPY . .

# Run as non-root.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser /app
USER appuser

EXPOSE 8000

# Image is process-agnostic (same image runs uvicorn, celery worker, celery beat).
# Healthchecks live at the orchestration layer (DO app spec / docker-compose.yml).

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
