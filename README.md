# drf-blog-api

> ⚠️ **This project is currently under active development.** Expect breaking changes, incomplete features, and evolving documentation.

A RESTful Blog API built with **Django REST Framework**, featuring JSON:API compliance, JWT authentication, media file uploads, background task processing, usage metrics tracking, and OpenAPI documentation generation.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Framework | Django 5.x + Django REST Framework |
| API Spec | JSON:API (`djangorestframework-jsonapi`) |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Schema | OpenAPI 3.0 (`drf-spectacular`) |
| Storage | AWS S3 / Google Cloud Storage (`django-storages`) |
| Tasks | Django Q2 (background job queue) |
| Database | MySQL (production) / SQLite (dev) |
| Containerization | Docker + Docker Compose |
| Linting | Ruff |
| Testing | pytest + pytest-django |

---

## Apps

- **`accounts`** — User registration, roles, and JWT authentication
- **`content`** — Blog posts and content management
- **`uploads`** — Media file upload handling (S3/GCS support)
- **`metrics`** — Usage and event metrics tracking

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (package manager)
- Docker & Docker Compose

### Local Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/drf-blog-api.git
cd drf-blog-api

# Create virtual environment and install dependencies
uv sync --group dev --group test

# Activate the virtual environment
source .venv/bin/activate

# Copy and configure environment variables
cp .env.example .env.dev

# Run migrations
python src/manage.py migrate

# Start the development server
python src/manage.py runserver
