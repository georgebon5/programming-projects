# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.0] — 2026-04-03

### Added

#### Authentication & Security
- JWT token blacklist using `jti` claims to invalidate tokens server-side
- Refresh token rotation — each use issues a new refresh token and revokes the old one
- `POST /auth/logout` endpoint to explicitly revoke the current session
- Password change now revokes all active tokens for the user
- TOTP-based two-factor authentication (2FA) support
- Input sanitization for chat messages (HTML stripping to prevent XSS)

#### API & Middleware
- `X-Request-ID` middleware for end-to-end request tracing
- Security headers middleware (HSTS, X-Frame-Options, X-Content-Type-Options, etc.)
- Body size limit middleware to prevent oversized payload attacks
- API key rate limiting

#### Documents
- Soft delete for documents (`deleted_at` timestamp, restore, and hard-purge endpoints)
- Document reprocessing — single document and bulk reprocessing endpoints
- Bulk document upload endpoint

#### Chat & Conversations
- Chat conversation pagination with `skip`/`limit` query parameters and `X-Total-Count` response header

#### Webhooks
- Webhook system: full CRUD, HMAC-SHA256 payload signing, delivery tracking and retry logic

#### Caching
- Redis caching layer (`CacheService`) with tenant-scoped key namespacing

#### Observability
- 13 custom Prometheus metrics covering documents, chat, auth, vector store, and cache operations
- OpenTelemetry distributed tracing support (opt-in, Jaeger exporter)
- Alertmanager integration with 10 pre-configured alert rules
- Sentry error monitoring (opt-in via `SENTRY_DSN` environment variable)

#### Infrastructure & Kubernetes
- ChromaDB HTTP client mode for production deployments
- ChromaDB Kubernetes StatefulSet manifest
- Kubernetes network policies for pod-to-pod traffic control
- Pod Disruption Budgets (PDBs) for zero-downtime rolling updates
- Sealed Secrets integration for encrypted Kubernetes secret management
- PostgreSQL Kubernetes StatefulSet with persistent storage

#### Billing & Compliance
- Stripe billing integration: checkout sessions, customer portal, and webhook handling
- GDPR data export endpoint (`GET /me/export`) — full user data as JSON
- GDPR account deletion endpoint (`DELETE /me/account`) with cascade cleanup

#### Testing
- Integration tests using `testcontainers` with a real PostgreSQL instance
- Alembic migration round-trip tests (upgrade + downgrade)
- pytest coverage enforcement at 80% threshold (current coverage ~84%)

### Changed
- Expired token cleanup is now handled automatically via Celery beat schedule; also exposed as an admin endpoint for on-demand execution

---

## [0.4.0] — Operations

### Added
- Celery + Redis worker setup for asynchronous background task processing
- Prometheus metrics endpoint and pre-built Grafana dashboards
- Docker Compose configuration for local development and integration testing
- Kubernetes manifests: Deployments, Horizontal Pod Autoscaler (HPA), Ingress, and PersistentVolumeClaims
- Liveness and readiness health check probes
- Structured JSON logging throughout the application

---

## [0.3.0] — Communication & Security

### Added
- WebSocket chat endpoint with real-time token streaming
- Email service: password reset and email verification flows
- Per-endpoint and per-tenant rate limiting
- CORS configuration with configurable allowed origins
- S3-compatible storage backend as an alternative to local disk storage

---

## [0.2.0] — Core Features

### Added
- User management: invite flow, full CRUD, and role-based access control (`admin` / `member`)
- Tenant settings management and configurable usage quotas
- Dashboard endpoint exposing aggregated usage statistics
- Audit logging for all mutating operations
- Document search and filtering by filename and processing status
- API key authentication as an alternative to JWT bearer tokens

---

## [0.1.0] — Foundation

### Added
- FastAPI application with multi-tenant architecture and tenant isolation at every layer
- PostgreSQL database with SQLAlchemy ORM and Alembic for schema migrations
- JWT-based authentication: tenant admin registration and login
- Document upload with text extraction support for PDF, DOCX, and TXT formats
- Automatic document chunking pipeline
- ChromaDB vector storage with per-tenant collection isolation
- Basic RAG chat endpoint (HTTP, synchronous)

---

[0.5.0]: https://github.com/your-org/multi-tenant-rag/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/your-org/multi-tenant-rag/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/your-org/multi-tenant-rag/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/your-org/multi-tenant-rag/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/your-org/multi-tenant-rag/releases/tag/v0.1.0
