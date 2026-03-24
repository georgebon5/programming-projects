# Multi-Tenant AI RAG System

Production-ready FastAPI backend for tenant-isolated document intelligence.

## Features
- Multi-tenant architecture with strict tenant data isolation
- JWT authentication and role-based access control (admin/member/viewer)
- User lifecycle management (invite, update, deactivate, delete, password change)
- Document upload, processing, and vector indexing (txt, md, pdf, docx)
- RAG chat endpoint with conversation history
- Admin dashboard endpoint for tenant stats and recent activity
- Rate limiting on sensitive endpoints (auth and chat)

## Stack
- FastAPI
- SQLAlchemy
- SQLite (dev) / PostgreSQL (docker)
- ChromaDB
- OpenAI SDK (with fallback mode if API key is missing)
- Pytest

## Project Status
1. Phase 1: Project setup and models - complete
2. Phase 2: Authentication and RBAC - complete
3. Phase 2.5: User management - complete
4. Phase 3: Document upload and CRUD - complete
5. Phase 4: Processing pipeline (extract, chunk, embed) - complete
6. Phase 5: RAG chat and history - complete

## Local Run
```bash
cd "Multi-Tenant AI RAG System"

pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs:
- http://localhost:8000/docs

## Docker Run (DB)
```bash
docker-compose up -d db
```

## Testing
```bash
python3 -m pytest tests/ -q
```

Current suite coverage includes auth, users, documents, chat, dashboard, and rate limiting.

## Important Endpoints
- `POST /api/v1/auth/register-tenant-admin`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/users/invite`
- `POST /api/v1/documents/upload`
- `POST /api/v1/chat/`
- `GET /api/v1/chat/{conversation_id}`
- `GET /api/v1/admin/dashboard/`

## Security Notes
- Tenant isolation is enforced using `tenant_id`
- JWT contains tenant context and role claims
- Password hashing with bcrypt
- Role checks at endpoint level
- Rate limits reduce auth/chat abuse
