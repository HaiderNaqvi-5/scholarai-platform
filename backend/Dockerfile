# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=600 --retries 10 \
    --find-links=/wheels -r requirements.txt

COPY . .

# Security: Run as non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Image is process-agnostic (same image runs uvicorn, celery worker, celery beat).
# Healthchecks live at the orchestration layer (docker-compose.yml / k8s manifests),
# not baked into the image. Each service defines a check appropriate to its process.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
