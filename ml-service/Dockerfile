# ── Stage 1: Builder ─────────────────────────────────────────────────────────
# Use a full Python image to install heavy dependencies (prophet, xgboost etc.)
# then copy only what's needed into the final slim image.
FROM python:3.11-slim AS builder

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install system dependencies needed to compile prophet/cmdstanpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (Docker layer caching:
# if requirements.txt hasn't changed, this layer is reused on rebuild)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production image ─────────────────────────────────────────────────
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Production defaults — overridden by Render environment variables
    APP_ENV=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    MODEL_VERSION=v1

WORKDIR /app

# Copy installed packages from builder stage (avoids reinstalling)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/        ./app/
COPY ml/         ./ml/
COPY saved_models/ ./saved_models/
COPY data/       ./data/
COPY .env.example ./.env.example

# Non-root user for security (never run containers as root in production)
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app
USER appuser

# Expose the port Render will route traffic to
EXPOSE 8000

# Health check — Render uses this to know if your container is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Production server: 2 uvicorn workers, no --reload, proper timeout
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--timeout-keep-alive", "30", \
     "--access-log"]
