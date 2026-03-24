# Multi-Tenant AI RAG System

Production-ready FastAPI backend for tenant-isolated document intelligence. Upload documents, process them into embeddings, and chat with your data using RAG (Retrieval-Augmented Generation).

## Features

### Core
- **Multi-tenant architecture** — strict data isolation per tenant via `tenant_id` on every query
- **JWT authentication** — HS256 tokens with 24 h expiry
- **RBAC** — three roles: `admin`, `member`, `viewer` enforced at endpoint level
- **User management** — invite, update, deactivate, delete, change password

### Documents & RAG
- **File upload** — supports `.txt`, `.md`, `.pdf`, `.docx` (configurable max size)
- **Background processing** — text extraction → chunking (500 tokens, 50 overlap) → ChromaDB vector indexing, runs as a FastAPI background task
- **RAG chat** — semantic search over tenant documents + LLM generation (OpenAI gpt-4o-mini, with fallback mode if no API key)
- **Conversation history** — per-user, per-tenant conversation tracking

### Operations
- **Alembic migrations** — versioned schema management with SQLite batch mode support
- **Structured JSON logging** — machine-readable in production, human-readable in dev
- **Rate limiting** — per-user limits on auth (5–10/min) and chat (20/min)
- **Audit logging** — immutable log of all user actions (login, upload, delete, settings, etc.)
- **Tenant quotas** — configurable limits on users, documents, storage, and daily chat messages
- **Admin dashboard** — tenant stats, storage usage, recent activity
- **Health check** — `/health` with uptime, version, Python version, environment

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.104 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic 1.12 |
| Database | SQLite (dev) / PostgreSQL 15 (production) |
| Vector DB | ChromaDB 0.4 |
| LLM | OpenAI gpt-4o-mini (optional — works without API key in fallback mode) |
| Auth | python-jose (JWT), bcrypt |
| Rate Limiting | slowapi |
| Document parsing | pdfplumber, python-docx |
| Tokenizer | tiktoken |
| Testing | pytest |

## Project Structure

```
app/
├── main.py                  # FastAPI app, middleware, routers
├── config.py                # Pydantic Settings (.env)
├── api/v1/                  # Route handlers
│   ├── auth.py              # Register, login, me
│   ├── users.py             # Invite, list, update, delete
│   ├── documents.py         # Upload, list, get, delete, process, search
│   ├── chat.py              # RAG chat, conversation history
│   ├── dashboard.py         # Admin stats
│   ├── audit_logs.py        # Audit log queries
│   └── settings.py          # Tenant settings & quotas
├── models/                  # SQLAlchemy models
├── schemas/                 # Pydantic request/response schemas
├── services/                # Business logic
│   ├── auth_service.py
│   ├── document_service.py
│   ├── processing_service.py  # Extract → chunk → embed pipeline
│   ├── chat_service.py       # RAG query with context retrieval
│   ├── vector_store.py        # ChromaDB operations
│   ├── text_extractor.py
│   ├── chunker.py
│   ├── audit_service.py
│   ├── dashboard_service.py
│   └── tenant_settings_service.py
├── dependencies/auth.py     # JWT dependency injection
├── db/database.py           # Engine, SessionLocal, Base
└── utils/
    ├── security.py          # Password hashing, JWT encode/decode
    ├── exceptions.py        # Custom exceptions
    ├── rate_limit.py        # SlowAPI config
    └── logging.py           # Structured JSON logging
alembic/                     # Alembic migrations
tests/                       # Pytest test suite (58+ tests)
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/georgebon5/programming-projects.git
cd "Multi-Tenant AI RAG System"
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET_KEY to a random string
```

### 3. Run migrations (or auto-create tables)

```bash
# Using Alembic (recommended for production):
python3 -m alembic upgrade head

# Tables are also auto-created on startup for dev convenience.
```

### 4. Start the server

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

### Docker

```bash
docker-compose up -d
```

This starts PostgreSQL 15 + the app. Runs on port 8000.

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register-tenant-admin` | Register new tenant + admin user |
| POST | `/api/v1/auth/login` | Login, returns JWT |
| GET | `/api/v1/auth/me` | Current user info |

### Users
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/users/invite` | Invite user to tenant (admin only) |
| GET | `/api/v1/users/` | List tenant users |
| GET | `/api/v1/users/{id}` | Get user details |
| PUT | `/api/v1/users/{id}` | Update user role/status (admin only) |
| DELETE | `/api/v1/users/{id}` | Delete user (admin only) |
| PUT | `/api/v1/users/me/password` | Change own password |

### Documents
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/documents/upload` | Upload document (returns immediately, processes in background) |
| POST | `/api/v1/documents/{id}/process` | Re-trigger processing |
| GET | `/api/v1/documents/` | List documents (with `?status=` and `?search=` filters) |
| GET | `/api/v1/documents/{id}` | Get document details |
| DELETE | `/api/v1/documents/{id}` | Delete document + vectors |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat/` | RAG query against tenant documents |
| GET | `/api/v1/chat/{conversation_id}` | Get conversation history |

### Admin
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/dashboard/` | Tenant stats & recent activity |
| GET | `/api/v1/audit-logs/` | Query audit logs (with filters) |
| GET | `/api/v1/settings/` | Get tenant settings |
| PUT | `/api/v1/settings/` | Update tenant settings (admin only) |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check with uptime & version |
| GET | `/` | Root info |

## Database Migrations

```bash
# Check current revision
python3 -m alembic current

# Create a new migration after model changes
python3 -m alembic revision --autogenerate -m "description"

# Apply migrations
python3 -m alembic upgrade head

# Rollback one step
python3 -m alembic downgrade -1
```

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -q

# Run with verbose output
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_auth.py -v
```

Test suite covers: authentication, user management, document CRUD, chat, dashboard, rate limiting, audit logs, tenant settings, and document search.

## Security

- Tenant isolation enforced via `tenant_id` on every database query
- JWT tokens contain tenant context and role claims
- Password hashing with bcrypt (12 rounds)
- Role-based endpoint access (admin / member / viewer)
- Rate limiting on authentication and chat endpoints
- Immutable audit logging of all sensitive actions
- CORS restricted in production mode
- Swagger docs disabled in production
