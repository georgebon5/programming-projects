# Contributing to Multi-Tenant AI RAG System

Thank you for your interest in contributing. This guide covers everything you need to get started.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Database Migrations](#database-migrations)
- [Code Style](#code-style)
- [Pull Request Conventions](#pull-request-conventions)
- [Project Structure](#project-structure)

---

## Prerequisites

- Python 3.12+
- Docker and Docker Compose (for PostgreSQL, Redis, and ChromaDB)
- An OpenAI API key (required for chat and embedding features)

---

## Development Setup

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd multi-tenant-ai-rag-system
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and fill in your values (database URL, Redis URL, OpenAI API key, etc.).

5. **Start backing services**

   ```bash
   docker compose up -d db redis
   ```

6. **Apply database migrations**

   ```bash
   alembic upgrade head
   ```

7. **Start the application**

   ```bash
   uvicorn app.main:app --reload
   ```

8. **Start the Celery worker** (in a separate terminal, with the virtual environment activated)

   ```bash
   celery -A app.worker worker --loglevel=info
   ```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

## Running Tests

Unit tests use SQLite and do not require Docker. Integration tests spin up a PostgreSQL container via testcontainers.

**Run all unit tests**

```bash
pytest tests/
```

**Run integration tests** (requires Docker)

```bash
pytest tests/integration/
```

**Run a single test file**

```bash
pytest tests/test_auth.py -v
```

**Skip the coverage threshold check**

```bash
pytest --override-ini="addopts=" tests/
```

Coverage is enforced at 80% minimum. The coverage source is the `app/` package; `tracing.py` and `worker.py` are excluded from measurement. All new features must include tests that keep coverage at or above this threshold.

---

## Database Migrations

Migrations are managed with Alembic. All migration files live in `alembic/`.

**Create a new migration** (autogenerate from model changes)

```bash
alembic revision --autogenerate -m "short description of change"
```

**Apply all pending migrations**

```bash
alembic upgrade head
```

**Roll back the last migration**

```bash
alembic downgrade -1
```

**Check current migration state**

```bash
alembic current
```

### Migration rules

- Always use `batch_alter_table` when modifying existing tables. This is required for SQLite compatibility (used in tests).
- Name all constraints explicitly — never use `None` as a constraint name. Anonymous constraints break SQLite batch mode.
- Migration correctness is verified automatically in CI via `tests/test_migrations.py`.

---

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting. Configuration is in `pyproject.toml`.

**Run the linter and formatter**

```bash
ruff check app/ tests/
ruff format app/ tests/
```

Key settings:

- Target Python version: 3.12
- Line length: 120 characters
- Active rule sets: `E`, `W`, `F`, `I`, `UP`, `B`, `SIM`
- Ignored rules: `E501`, `B008`, `UP007`, `UP042`
- `app` is treated as a first-party package for import sorting

### Architecture conventions

Follow the layered architecture used throughout the codebase:

```
routers (app/api/v1/)  ->  services (app/services/)  ->  models (app/models/)
```

- Route handlers in `app/api/v1/` are thin — delegate all business logic to services.
- Use Pydantic schemas (`app/schemas/`) for all request and response validation.
- Do not put business logic directly in route handlers or models.

---

## Pull Request Conventions

- **One feature or fix per PR.** Keep the scope focused.
- **Descriptive title.** The title should make the change clear without needing to read the description.
- **Include tests.** Every new feature or bug fix must be accompanied by tests.
- **All tests must pass.** `pytest` must exit with code 0.
- **Coverage must stay at or above 80%.** PRs that drop coverage below the threshold will not be merged.

---

## Project Structure

```
app/
  api/v1/        — Route handlers
  models/        — SQLAlchemy models
  schemas/       — Pydantic schemas
  services/      — Business logic
  dependencies/  — FastAPI dependencies (auth)
  utils/         — Helpers (security, metrics, logging, etc.)
  db/            — Database setup
  config.py      — Settings loaded from environment variables
  main.py        — Application entry point
  worker.py      — Celery task definitions

tests/             — Unit tests (SQLite, no Docker required)
tests/integration/ — Integration tests (PostgreSQL via testcontainers)

alembic/           — Database migration scripts
k8s/               — Kubernetes manifests
monitoring/        — Prometheus, Grafana, and Alertmanager configuration
frontend/          — SPA frontend
```
