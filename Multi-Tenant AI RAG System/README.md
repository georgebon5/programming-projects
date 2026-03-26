# Multi-Tenant AI RAG System

Production-ready FastAPI backend for tenant-isolated document intelligence. Upload documents, process them into embeddings, and chat with your data using RAG (Retrieval-Augmented Generation).

## Features

### Core
- **Multi-tenant architecture** — strict data isolation per tenant via `tenant_id` on every query
- **JWT authentication** — HS256 tokens with 24 h expiry + refresh tokens
- **RBAC** — three roles: `admin`, `member`, `viewer` enforced at endpoint level
- **User management** — invite, update, deactivate, delete, change password
- **Two-Factor Authentication** — TOTP (RFC 6238) via authenticator apps, with QR code provisioning
- **Email verification** — verify user email on registration (console backend in dev, SMTP in prod)
- **Password reset** — forgot/reset password flow via email tokens

### Documents & RAG
- **File upload** — supports `.txt`, `.md`, `.pdf`, `.docx` (configurable max size)
- **Pluggable storage** — local filesystem (default) or S3-compatible object storage (AWS, MinIO, DigitalOcean Spaces)
- **Background processing** — text extraction → chunking (500 tokens, 50 overlap) → ChromaDB vector indexing. Supports **Celery + Redis** (production) with automatic fallback to FastAPI BackgroundTasks (dev)
- **RAG chat** — semantic search over tenant documents + LLM generation (OpenAI gpt-4o-mini, with fallback mode if no API key)
- **WebSocket streaming** — real-time token-by-token streaming of RAG responses via `ws://host/api/v1/chat/ws`
- **Conversation history** — per-user, per-tenant conversation tracking
- **Document download** — download original uploaded files

### Billing & Subscriptions
- **Stripe integration** — checkout sessions, billing portal, webhook handling
- **Subscription tiers** — free / pro / enterprise mapped to tenant quotas

### Operations
- **Alembic migrations** — versioned schema management with SQLite batch mode support
- **Structured JSON logging** — machine-readable in production, human-readable in dev
- **Rate limiting** — per-user limits on auth (5–10/min) and chat (20/min)
- **Audit logging** — immutable log of all user actions (login, upload, delete, settings, etc.)
- **Tenant quotas** — configurable limits on users, documents, storage, and daily chat messages
- **Admin dashboard** — tenant stats, storage usage, recent activity
- **Security headers** — X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP, HSTS
- **Account lockout** — DB-persistent lockout after configurable failed login attempts

### Infrastructure
- **Docker** — multi-stage build, non-root user, healthchecks
- **Docker Compose** — PostgreSQL + Redis + App + Celery worker + pgAdmin
- **CI/CD** — GitHub Actions (lint, security scan, tests on Python 3.12+3.13, Docker build, deploy)
- **Kubernetes** — production-ready manifests (Deployment, Service, Ingress, ConfigMap, Secrets, PVC)
- **Monitoring** — Prometheus metrics at `/metrics` + Grafana dashboard provisioning
- **Database backup** — automated pg_dump scripts with retention & restore
- **Load testing** — Locust test suite for auth, documents, chat, and admin endpoints
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
| Auth | python-jose (JWT), bcrypt, pyotp (TOTP 2FA) |
| Rate Limiting | slowapi |
| Document parsing | pdfplumber, python-docx |
| Task Queue | Celery + Redis (optional) |
| Object Storage | Local filesystem / AWS S3 / MinIO (boto3) |
| Billing | Stripe |
| Monitoring | Prometheus + Grafana |
| Load Testing | Locust |
| CI/CD | GitHub Actions |
| Container | Docker, Kubernetes |
| Testing | pytest |

## Project Structure

```
app/
├── main.py                  # FastAPI app, middleware, routers
├── config.py                # Pydantic Settings (.env)
├── worker.py                # Celery worker & tasks
├── api/v1/                  # Route handlers
│   ├── auth.py              # Register, login, 2FA, password reset, email verify
│   ├── users.py             # Invite, list, update, delete
│   ├── documents.py         # Upload, list, get, download, delete, process
│   ├── chat.py              # RAG chat, WebSocket streaming, conversation history
│   ├── billing.py           # Stripe checkout, portal, webhooks
│   ├── dashboard.py         # Admin stats
│   ├── audit_logs.py        # Audit log queries
│   ├── settings.py          # Tenant settings & quotas
│   ├── api_keys.py          # API key management
│   └── export.py            # Data export
├── models/                  # SQLAlchemy models
├── schemas/                 # Pydantic request/response schemas
├── services/                # Business logic
│   ├── auth_service.py
│   ├── document_service.py
│   ├── processing_service.py  # Extract → chunk → embed pipeline
│   ├── chat_service.py       # RAG query with streaming support
│   ├── vector_store.py        # ChromaDB operations
│   ├── storage.py             # Pluggable file storage (local/S3)
│   ├── billing_service.py     # Stripe subscription management
│   ├── totp_service.py        # Two-factor authentication
│   ├── email_service.py       # Email sending (console/SMTP)
│   ├── password_reset_service.py
│   ├── email_verification_service.py
│   ├── audit_service.py
│   ├── dashboard_service.py
│   └── tenant_settings_service.py
├── dependencies/auth.py     # JWT dependency injection
├── db/database.py           # Engine, SessionLocal, Base
└── utils/
    ├── security.py          # Password hashing, JWT encode/decode
    ├── exceptions.py        # Custom exceptions
    ├── middleware.py         # Security headers, request logging, body size limit
    ├── rate_limit.py        # SlowAPI config
    └── logging.py           # Structured JSON logging
alembic/                     # Alembic migrations
k8s/                         # Kubernetes deployment manifests
monitoring/                  # Prometheus & Grafana provisioning
scripts/                     # Backup/restore scripts
tests/                       # Pytest test suite (126+ tests)
tests/load/                  # Locust load testing
frontend/                    # Vanilla JS SPA frontend
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
| GET | `/metrics` | Prometheus metrics |
| GET | `/` | Root info |
| WS | `/api/v1/chat/ws?token=JWT` | WebSocket streaming RAG chat |

### Billing
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/billing/checkout` | Create Stripe checkout session |
| POST | `/api/v1/billing/portal` | Stripe billing portal |
| GET | `/api/v1/billing/status` | Current subscription status |
| POST | `/api/v1/billing/webhook` | Stripe webhook receiver |

### Two-Factor Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/2fa/enable` | Generate TOTP secret + QR code |
| POST | `/api/v1/auth/2fa/verify` | Verify TOTP code and activate 2FA |
| POST | `/api/v1/auth/2fa/disable` | Disable 2FA (requires valid code) |

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
- Two-factor authentication (TOTP) support
- Role-based endpoint access (admin / member / viewer)
- Rate limiting on authentication and chat endpoints
- Account lockout after failed login attempts (DB-persistent)
- Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- Immutable audit logging of all sensitive actions
- CORS restricted in production mode
- Swagger docs disabled in production
- Body size limiting middleware

## Production Deployment

### Docker Compose (simple)

```bash
# Start all services (PostgreSQL, Redis, App, Celery Worker)
docker-compose up -d

# With monitoring stack
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secret.yml   # Edit with real secrets first!
kubectl apply -f k8s/pvc.yml
kubectl apply -f k8s/redis.yml
kubectl apply -f k8s/api-deployment.yml
kubectl apply -f k8s/worker-deployment.yml
kubectl apply -f k8s/ingress.yml
```

### Database Backup

```bash
# Manual backup
./scripts/backup_db.sh

# Restore from backup
./scripts/restore_db.sh backups/multi_tenant_rag_20240101_120000.dump

# Schedule daily backup via cron
echo "0 2 * * * /path/to/scripts/backup_db.sh" | crontab -
```

### Monitoring

The app exposes Prometheus metrics at `/metrics`. The monitoring stack includes:
- **Prometheus** — scrapes metrics every 15s
- **Grafana** — pre-provisioned dashboards for request rate, latency, errors, memory

Access Grafana at `http://localhost:3001` (default: admin/admin).

### Load Testing

```bash
pip install locust
locust -f tests/load/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 to configure and run tests
```
