# Build stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# Dev build stage
FROM builder AS builder-dev

RUN uv sync --frozen --dev

# Runtime stage
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --no-log-init app-user

WORKDIR /app

COPY --from=builder  /app/.venv /app/.venv

COPY --chown=app-user:app-user . .

RUN mkdir -p src/staticfiles src/media \
    && chown -R app-user:app-user src/staticfiles src/media

RUN chmod +x /app/entrypoint.sh

USER app-user

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "config.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--timeout", "60"]

# Dev runtime stage
FROM runtime AS runtime-dev

COPY --from=builder-dev --chown=app-user:app-user /app/.venv /app/.venv
