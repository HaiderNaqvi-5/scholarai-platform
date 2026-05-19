# Stage 1: Builder
# Microsoft's Playwright Python image ships with Chromium + all OS deps pre-installed
# at /ms-playwright. Avoids the `playwright install --with-deps chromium` step that
# OOM'd DO's App Platform builder. Scraper Celery worker launches Chromium at runtime
# exactly as before.
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# jammy base has python3 + build-essential + gcc; only need libpq-dev for asyncpg/psycopg2.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runtime
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=600 --retries 10 \
    --find-links=/wheels -r requirements.txt

# Chromium lives at /ms-playwright in the Microsoft base image. Export the path
# so the Python playwright SDK locates it at runtime.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY . .

# Run as non-root. /ms-playwright is world-readable in the base image so no chown
# needed there.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser /app
USER appuser

EXPOSE 8000

# Image is process-agnostic (same image runs uvicorn, celery worker, celery beat).
# Healthchecks live at the orchestration layer (DO app spec / docker-compose.yml),
# not baked into the image. Each component declares a check appropriate to its process.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
