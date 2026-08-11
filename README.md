# Simple DRF Blog API

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![Django](https://img.shields.io/badge/Django-5.2%2B-darkgreen)
![DRF](https://img.shields.io/badge/DRF-3.16%2B-red)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)
![Ruff](https://img.shields.io/badge/linted%20with-ruff-black)

> ⚠️ **This project is currently under active development.** Expect breaking changes, incomplete features, and evolving documentation.

A RESTful Blog API built with **Django REST Framework**, featuring JSON:API compliance, JWT authentication, role-based access control, media file uploads, Celery background task processing, usage metrics tracking, and OpenAPI documentation.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Apps](#apps)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Docker (recommended)](#option-a-docker-development-recommended)
  - [Local (without Docker)](#option-b-local-without-docker)
  - [Production](#production-deployment)
- [Environment Variables](#environment-variables)
- [API Overview](#api-overview)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Background Tasks](#background-tasks)
- [License](#license)

---

## Features

- **JSON:API compliant** request/response format (`application/vnd.api+json`) with dasherized field names, pagination, filtering, sorting, and search
- **JWT authentication** with refresh-token rotation and blacklisting (`djangorestframework-simplejwt`)
- **Role-based access control** — Admin and Editor roles implemented as proxy models with per-action permissions
- **Blog content management** — posts with draft/published/archived status, soft-delete (trash/restore), categories, tags, thumbnails, and attachments
- **Media uploads** — local filesystem storage; soft-delete with a scheduled cleanup task
- **Usage metrics** — post-view tracking middleware with bot filtering, Do-Not-Track respect, and Redis-based deduplication
- **Health checks** — API, database, and storage liveness endpoints
- **OpenAPI 3.0 documentation** — Swagger UI and ReDoc via drf-spectacular
- **Rate throttling** — per-endpoint throttle scopes (login, token refresh, uploads, writes, …)
- **Observability** — optional Sentry integration in production

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Framework | Django 5.2 + Django REST Framework 3.16 |
| API Spec | JSON:API (`djangorestframework-jsonapi`) |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Schema | OpenAPI 3.0 (`drf-spectacular`) |
| Storage | Local filesystem (Django default) |
| Task Queue | Celery 5 + Redis (broker, result backend & cache) |
| Database | MariaDB 11.8 (Docker) / SQLite (local fallback & tests) |
| Web Server | Gunicorn + nginx (TLS, reverse proxy) |
| Monitoring | Sentry (optional) |
| Containerization | Docker + Docker Compose |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Linting / Formatting | Ruff (+ pre-commit hooks) |
| Testing | pytest + pytest-django + factory-boy |

---

## Apps

- **`accounts`** — Custom user model with Admin/Editor roles, profiles, JWT authentication, password management
- **`content`** — Blog posts, categories, and tags; post workflow (status changes, trash/restore, thumbnails, attachments)
- **`uploads`** — Media file upload handling and soft-delete cleanup
- **`metrics`** — Health-check endpoints, post-view event tracking, and usage metrics

---

## Project Structure

```
├── docker-compose.yml          # Production stack (nginx, gunicorn, MariaDB, Redis, Celery)
├── docker-compose.dev.yml      # Development stack (Django runserver on :8000)
├── Dockerfile                  # Multi-stage build (runtime / runtime-dev targets)
├── entrypoint.sh               # Container entrypoint (collectstatic for the migrate service)
├── pyproject.toml              # Dependencies, pytest, Ruff and coverage config
├── .env.example                # Annotated environment variable reference
├── nginx/                      # Reverse-proxy config, TLS snippets, self-signed cert script
└── src/
    ├── manage.py
    ├── config/                 # Project settings (base / development / production / tests),
    │                           # URL routing, DRF router, Celery app, throttles
    ├── apps/
    │   ├── accounts/           # Users, profiles, roles, permissions
    │   ├── content/            # Posts, categories, tags
    │   ├── uploads/            # Upload models, cleanup task
    │   └── metrics/            # Health checks, event bus, tracking middleware
    ├── tests/                  # Shared factories, helpers, integration tests
    └── utils/                  # Base models, exception handler, text tools
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (package manager)
- Docker & Docker Compose (for the containerized stack)

### Option A: Docker Development (recommended)

Spins up MariaDB, Redis, the Django dev server (with auto-migrations), a Celery worker, and Celery beat. The API is exposed on `http://localhost:8000`.

```bash
# Clone the repo
git clone https://github.com/<your-username>/simple-drf-blog.git
cd simple-drf-blog

# Configure environment (edit passwords/secrets as needed)
cp .env.example .env

# Build and start the full dev stack
docker compose -f docker-compose.dev.yml up --build

# (in another terminal) create an admin user
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

> **Note:** You don't need to set `DATABASE_URL` for Docker — the compose files build
> it from the `MARIADB_*` variables and inject it into every app service. (It is
> intentionally absent from `.env.example`: `dj-database-url` reads it from the
> process environment, not from `.env`.)

### Option B: Local (without Docker)

Uses SQLite and the in-process cache by default — no database or Redis server needed for a quick look. (Cache errors and post-view event dispatch are silently ignored when Redis is unavailable; run the Docker stack for full functionality.)

```bash
# Clone the repo
git clone https://github.com/<your-username>/simple-drf-blog.git
cd simple-drf-blog

# Create virtual environment and install dependencies
uv sync --group dev --group test

# Activate the virtual environment
source .venv/bin/activate

# Copy and configure environment variables
cp .env.example .env

# Run migrations (SQLite database at src/db.sqlite3)
python src/manage.py migrate

# Create an admin user
python src/manage.py createsuperuser

# Start the development server
python src/manage.py runserver
```

To use MariaDB locally instead of SQLite, **export** `DATABASE_URL` in your shell
(e.g. `export DATABASE_URL=mysql://user:password@localhost:3306/dbname`) before
running `manage.py` — setting it only in `.env` has no effect.

### Production Deployment

The production compose stack runs Gunicorn behind nginx (ports 80/443, HTTP→HTTPS redirect, self-signed TLS cert by default), plus MariaDB, Redis, Celery worker/beat, and a one-shot migration service.

```bash
# Configure secrets
cp .env.example .env
# Edit .env: SECRET_KEY, ALLOWED_HOSTS, MARIADB_*, REDIS_PASSWORD, CACHE_URL,
# CELERY_* URLs, DATABASE_URL — see the annotations in .env.example

# (optional) regenerate the self-signed certificate
./nginx/scripts/gen-self-signed.sh

# Build and start
docker compose up -d --build
```

To use Let's Encrypt or a custom certificate instead, see the instructions in the
comments at the top of `nginx/conf.d/blog.conf`.

Generate a strong `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Environment Variables

All variables except `DATABASE_URL` are documented inline in [`.env.example`](.env.example). Summary:

| Variable | Required | Description |
| --- | --- | --- |
| `SECRET_KEY` | prod | Django secret key |
| `DEBUG` | optional | Defaults to `True` in dev, `False` in prod/tests |
| `ALLOWED_HOSTS` | prod | Comma-separated host list |
| `NUM_PROXIES` | optional | Reverse proxies in front of the app (client-IP resolution). Default `1` prod, `0` dev |
| `MARIADB_DATABASE` / `MARIADB_USER` / `MARIADB_PASSWORD` / `MARIADB_ROOT_PASSWORD` | prod, dev (Docker) | MariaDB container bootstrap credentials |
| `DATABASE_URL` | local (non-Docker) only | e.g. `mysql://user:password@localhost:3306/dbname`; **export** it in your shell — setting it in `.env` has no effect. Docker derives it from `MARIADB_*` automatically. Falls back to SQLite |
| `CELERY_BROKER_URL` | prod | e.g. `redis://:<password>@redis:6379/0` |
| `CELERY_RESULT_BACKEND` | prod | e.g. `redis://:<password>@redis:6379/1` |
| `CACHE_URL` | prod | e.g. `redis://:<password>@redis:6379/2` |
| `REDIS_PASSWORD` | prod, dev (Docker) | Redis container password; must match the passwords embedded in the URLs above |
| `POST_VIEW_DEDUP_TTL` | optional | Post-view deduplication window in seconds (default `300` prod, `5` dev) |
| `SENTRY_DSN` | optional | Empty string disables Sentry |
| `ENVIRONMENT` | optional | Sentry environment tag (default `production`) |
| `API_VERSION` | optional | API metadata version (default `1.0`) |

---

## API Overview

Base URL (dev): `http://localhost:8000`. All resources are versioned under `/api/v1/` and speak JSON:API — send `Content-Type: application/vnd.api+json` for writes.

| What | URL |
| --- | --- |
| API root (discovery) | `GET /` |
| Swagger UI | `GET /api/v1/docs/` |
| ReDoc | `GET /api/v1/redoc/` |
| OpenAPI schema | `GET /api/v1/schema/` (admin only) |
| Django admin | `/admin/` |
| Health checks | `GET /health/`, `/health/database/`, `/health/storage/` |
| Usage metrics | `GET /metrics/` |

### Authentication

Users are created by admins (there is no public signup) — e.g. via `createsuperuser` or the Django admin.

```bash
# Obtain a token pair
curl -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "<username>", "password": "<password>"}'

# Refresh / verify / blacklist
POST /api/v1/token/refresh/
POST /api/v1/token/verify/
POST /api/v1/token/blacklist/
```

Use the access token as `Authorization: Bearer <access>`.

### Resources

| Endpoint | Description | Notes |
| --- | --- | --- |
| `/api/v1/posts/` | Blog posts | Public read; writes require Editor role |
| `/api/v1/categories/` | Post categories | |
| `/api/v1/tags/` | Post tags | |
| `/api/v1/uploads/` | Media uploads | Editor role required |
| `/api/v1/users/` | User management | Admin only (list/create/update/delete); `GET/PATCH /api/v1/users/me/` for self-service |
| `/api/v1/profiles/` | User profiles | `GET/PUT/PATCH /api/v1/profiles/me/` |

Notable sub-resource actions:

```
POST   /api/v1/posts/{slug}/change_status/          # draft / published / archived workflow
POST   /api/v1/posts/{slug}/restore/                # restore from trash
GET    /api/v1/posts/trash/                         # list soft-deleted posts
POST   /api/v1/posts/{slug}/thumbnail/              # set thumbnail
DELETE /api/v1/posts/{slug}/thumbnail/              # remove thumbnail
POST   /api/v1/posts/{slug}/attachments/            # attach uploads
DELETE /api/v1/posts/{slug}/attachments/{id}/       # detach an upload
POST   /api/v1/uploads/{id}/restore/
GET    /api/v1/uploads/trash/
POST   /api/v1/users/me/change-password/
POST   /api/v1/users/{id}/change_role/              # admin
POST   /api/v1/users/{id}/force_password_change/    # admin
POST   /api/v1/profiles/me/public/                  # toggle profile visibility
```

### Example: list and create posts

```bash
# List published posts (public)
curl http://localhost:8000/api/v1/posts/ \
  -H "Accept: application/vnd.api+json"

# Create a post (Editor role required)
curl -X POST http://localhost:8000/api/v1/posts/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
        "data": {
          "type": "posts",
          "attributes": {"title": "Hello World", "content": "My first post."},
          "relationships": {
            "category": {"data": {"type": "categories", "id": "1"}}
          }
        }
      }'
```

Lists are paginated (10 items per page by default) and support JSON:API `filter[...]`, `sort`, and `filter[search]` query parameters. Anonymous requests are throttled at 100 requests/hour, authenticated requests at 1000/hour (login: 10/hour, token endpoints: 5/minute).

The full request/response reference is generated from the code — see Swagger UI at `/api/v1/docs/`.

---

## Running Tests

Tests use an in-memory SQLite database, eager Celery execution, and relaxed throttles (`config.settings.tests`):

```bash
# From the project root (with the venv activated)
pytest

# With coverage
pytest --cov=src
```

---

## Code Quality

```bash
# Lint and auto-fix
ruff check --fix .

# Format
ruff format .

# Install git hooks (ruff + ruff-format + basic hygiene checks)
pre-commit install
```

---

## Background Tasks

Celery handles async work such as metrics ingestion and the daily cleanup of soft-deleted uploads older than 30 days (scheduled at 03:00 UTC via Celery beat). In Docker these run as dedicated services (`celery_worker`, `celery_beat`). To run them locally (requires a Redis broker):

```bash
cd src
celery -A config worker -l info
celery -A config beat -l info
```

---

## License

This project is licensed under the **GNU Affero General Public License v3.0** — see [LICENSE](LICENSE) for details.
