# Architecture — Multi-Tenant AI RAG System

This document describes the architecture of the Multi-Tenant AI RAG System (v0.5.0), a SaaS platform that lets organizations upload documents and query them via a Retrieval-Augmented Generation (RAG) pipeline backed by OpenAI GPT-4.

---

## C4 Context Diagram

Shows the system boundary and its relationships with external users and services.

```mermaid
C4Context
    title System Context — Multi-Tenant AI RAG System

    Person(tenantAdmin, "Tenant Admin", "Manages users, settings, billing, and document ingestion for a tenant organization")
    Person(endUser, "End User", "Asks questions against the tenant's document corpus via chat")

    System(ragSystem, "Multi-Tenant AI RAG System", "Ingests documents, generates embeddings, and answers questions using RAG")

    System_Ext(openai, "OpenAI API", "Chat completions (GPT-4) and embeddings (text-embedding-3-small)")
    System_Ext(stripe, "Stripe", "Subscription billing and payment processing")
    System_Ext(s3, "S3 / Local Storage", "Document file storage backend")
    System_Ext(smtp, "SMTP / Email", "Transactional email (verification, password reset, invites)")
    System_Ext(sentry, "Sentry", "Error monitoring (opt-in)")
    System_Ext(jaeger, "Jaeger", "Distributed tracing via OpenTelemetry (opt-in)")

    Rel(tenantAdmin, ragSystem, "Manages tenants, uploads docs, configures settings", "HTTPS")
    Rel(endUser, ragSystem, "Sends chat queries, views answers", "HTTPS / WebSocket")
    Rel(ragSystem, openai, "Generates embeddings and chat completions", "HTTPS")
    Rel(ragSystem, stripe, "Creates checkout sessions, handles webhooks", "HTTPS")
    Rel(ragSystem, s3, "Stores and retrieves document files", "HTTPS / local fs")
    Rel(ragSystem, smtp, "Sends transactional emails", "SMTP")
    Rel(ragSystem, sentry, "Reports exceptions", "HTTPS")
    Rel(ragSystem, jaeger, "Exports traces", "OTLP/gRPC")
```

---

## C4 Container Diagram

Shows every internal container and how they communicate.

```mermaid
C4Container
    title Container Diagram — Multi-Tenant AI RAG System

    Person(user, "User / Tenant Admin")

    Container(api, "FastAPI API", "Python / FastAPI", "REST + WebSocket API. Handles auth, documents, chat, billing, webhooks. Exposes /api/v1")
    Container(worker, "Celery Worker", "Python / Celery", "Processes document ingestion tasks, periodic cleanup, and retry logic")
    ContainerDb(postgres, "PostgreSQL", "Relational DB", "Stores users, tenants, documents, audit logs, conversations, webhooks, API keys")
    ContainerDb(redis, "Redis", "In-memory store", "Celery broker, response cache (CacheService), rate-limit counters")
    ContainerDb(chromadb, "ChromaDB", "Vector DB", "Stores document chunk embeddings, one collection per tenant")
    System_Ext(openai, "OpenAI API", "Embeddings + GPT-4 completions")
    System_Ext(s3, "S3 / Local Storage", "Document files")
    Container(prometheus, "Prometheus", "Metrics scraper", "Scrapes /metrics from API and worker")
    Container(grafana, "Grafana", "Dashboard", "Visualises Prometheus metrics")
    Container(alertmanager, "Alertmanager", "Alert router", "Routes alerts to Slack / email")

    Rel(user, api, "HTTP requests / WebSocket", "HTTPS")
    Rel(api, postgres, "Reads / writes application data", "asyncpg / SQLAlchemy")
    Rel(api, redis, "Caching, rate limiting", "redis-py")
    Rel(api, chromadb, "Similarity search, upsert chunks", "chromadb client")
    Rel(api, openai, "Embedding + chat completion requests", "HTTPS")
    Rel(api, s3, "Upload / download files", "boto3 / local fs")
    Rel(api, worker, "Enqueues background tasks", "Redis / Celery")
    Rel(worker, postgres, "Updates document status", "SQLAlchemy")
    Rel(worker, chromadb, "Upserts embedding chunks", "chromadb client")
    Rel(worker, openai, "Generates embeddings", "HTTPS")
    Rel(worker, s3, "Reads uploaded files", "boto3 / local fs")
    Rel(worker, redis, "Task queue / results backend", "redis-py")
    Rel(prometheus, api, "Scrapes metrics", "HTTP /metrics")
    Rel(grafana, prometheus, "Queries metrics", "PromQL")
    Rel(prometheus, alertmanager, "Fires alerts", "HTTP")
```

---

## Document Upload Flow

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI API
    participant Storage as S3 / Local Storage
    participant Redis
    participant Worker as Celery Worker
    participant OpenAI
    participant ChromaDB
    participant Postgres

    User->>API: POST /api/v1/documents/upload (file)
    API->>Postgres: Create document record (status=pending)
    API->>Storage: Persist raw file
    API->>Redis: Enqueue Celery task (process_document)
    API-->>User: 202 Accepted {document_id}

    Redis-->>Worker: Deliver task
    Worker->>Storage: Read file bytes
    Worker->>Worker: Extract text (PDF/DOCX/TXT)
    Worker->>Worker: Split text into token-based chunks
    Worker->>OpenAI: POST /embeddings (chunks)
    OpenAI-->>Worker: Embedding vectors
    Worker->>ChromaDB: Upsert chunks + vectors (tenant_{uuid} collection)
    Worker->>Postgres: Update document status=completed
```

---

## RAG Chat Query Flow

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI API
    participant Postgres
    participant ChromaDB
    participant OpenAI

    alt HTTP
        User->>API: POST /api/v1/chat/
    else WebSocket
        User->>API: WS /api/v1/chat/ws
    end

    API->>API: Sanitize and validate question
    API->>ChromaDB: Query tenant_{uuid} collection (top-k chunks)
    ChromaDB-->>API: Relevant document chunks
    API->>OpenAI: POST /chat/completions (system prompt + context + question)

    alt WebSocket (streaming)
        OpenAI-->>API: Stream tokens
        API-->>User: Stream tokens via WebSocket
    else HTTP
        OpenAI-->>API: Full response
        API-->>User: JSON response
    end

    API->>Postgres: Persist conversation message + metadata
```

---

## Multi-Tenant Isolation

Every database table includes a `tenant_id` foreign key. All ORM queries append a `WHERE tenant_id = <current_tenant>` predicate enforced at the service layer — there is no cross-tenant data leakage by construction.

| Layer | Isolation mechanism |
|---|---|
| PostgreSQL | `tenant_id` column on every model; service-layer query filters |
| ChromaDB | Separate collection per tenant: `tenant_{uuid}` |
| Rate limiting | Counters keyed by `tenant_id` + `user_id` in Redis |
| API keys | Scoped to a single tenant; validated on every request |
| Audit logs | Written per tenant; accessible only to that tenant's admins |

GDPR account deletion purges all tenant data: PostgreSQL rows, ChromaDB collections, stored files, and cached values.

---

## Infrastructure & Deployment

### Local Development

Docker Compose brings up the full stack: `postgres`, `redis`, `chromadb`, `app` (FastAPI + Uvicorn), `worker` (Celery), and `pgadmin`. A single `docker compose up` is sufficient to run the system locally.

### Production (Kubernetes)

Kubernetes manifests (in `k8s/`) provide:

- **Namespace** isolation per environment
- **Deployments** for the API and Celery worker with **HPA** (Horizontal Pod Autoscaler) and **PDB** (Pod Disruption Budget)
- **StatefulSets** for PostgreSQL and ChromaDB with persistent volume claims
- **Ingress** with TLS termination
- **NetworkPolicies** limiting pod-to-pod traffic to declared paths only
- **SealedSecrets** for encrypted secret management in Git

### Observability

| Tool | Role |
|---|---|
| Prometheus | Scrapes `/metrics` from API and worker |
| Grafana | Pre-built dashboards for request rates, latency, error rates, queue depth |
| Alertmanager | Routes firing alerts to Slack and/or email |
| Jaeger | Distributed tracing via OpenTelemetry (opt-in via `ENABLE_TRACING=true`) |
| Sentry | Exception tracking and performance monitoring (opt-in via `SENTRY_DSN`) |
