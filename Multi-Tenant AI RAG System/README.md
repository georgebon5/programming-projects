# README for Multi-Tenant AI RAG System

## Project Overview
A production-ready SaaS backend where different companies (tenants) can upload PDFs and query them using AI.

## Tech Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Authentication**: JWT
- **AI/RAG**: LangChain + OpenAI
- **Vector DB**: ChromaDB (or Pinecone)
- **DevOps**: Docker & Docker Compose

## Project Phases
1. **Phase 1** ✅ - Project Setup, Docker Compose, SQLAlchemy Models
2. **Phase 2** - JWT Authentication & RBAC
3. **Phase 3** - File Upload Handling
4. **Phase 4** - Document Processing (Chunking, Embeddings)
5. **Phase 5** - RAG Chat Endpoint

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Setup
```bash
# Clone the project
cd Multi-Tenant AI RAG System

# Create .env file
cp .env.example .env

# Start PostgreSQL
docker-compose up -d db

# Install dependencies
pip install -r requirements.txt

# Run migrations (Phase 1.5)
# alembic upgrade head

# Run the app
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## Directory Structure

See `STRUCTURE.md` for full directory tree.

## Development

### Code Quality
```bash
# Format code
black app/

# Lint
flake8 app/

# Sort imports
isort app/
```

### Testing
```bash
pytest tests/
```

## Security Notes
- All data is isolated by `tenant_id`
- JWT tokens contain tenant_id for verification
- Cascade deletes ensure GDPR compliance
- Passwords hashed with bcrypt

---

**Built for production-ready portfolio impact! 🚀**
