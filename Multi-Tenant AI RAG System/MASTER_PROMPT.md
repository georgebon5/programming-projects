# Master Implementation Prompt — Multi-Tenant AI RAG System

You are working on a **production-grade Multi-Tenant AI RAG System** built with FastAPI, SQLAlchemy, ChromaDB, OpenAI, Celery, Redis, PostgreSQL, and Docker/Kubernetes. The project is at version 0.5.0 and is functionally complete but needs hardening across security, observability, infrastructure, testing, data management, and API maturity.

Below is a **prioritized, phased implementation plan**. Each phase has clear deliverables, technical specifications, and acceptance criteria. Work through them **in order** — each phase builds on the previous. Follow the existing project conventions: layered architecture (routers → services → models), Pydantic schemas, Alembic migrations, pytest tests, and the established coding style.

**Critical rules:**
- Never break existing functionality. Run `pytest` after every significant change.
- Every new database change needs an Alembic migration.
- Every new feature needs tests (unit + integration where applicable).
- Follow existing patterns — don't reinvent what's already there.
- Keep PRs/commits atomic and focused. One phase = one logical unit of work.

---

## PHASE 1 — Security Hardening (HIGH PRIORITY)

### 1.1 JWT Token Blacklist & Refresh Token Rotation

**Problem:** If a JWT is stolen, it's valid for 24 hours with no way to revoke it. There's no refresh token rotation, so a compromised refresh token gives indefinite access.

**Implementation:**

1. Create a new model `app/models/token_blacklist.py`:
   ```python
   class BlacklistedToken(Base):
       __tablename__ = "blacklisted_tokens"
       id = Column(UUID, primary_key=True, default=uuid4)
       jti = Column(String, unique=True, nullable=False, index=True)  # JWT ID
       token_type = Column(String, nullable=False)  # "access" or "refresh"
       user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
       tenant_id = Column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"))
       blacklisted_at = Column(DateTime, default=func.now())
       expires_at = Column(DateTime, nullable=False)  # for cleanup
   ```

2. Update `app/utils/security.py`:
   - Add a `jti` (JWT ID, uuid4) claim to every token generated.
   - Reduce access token expiry to **15 minutes**.
   - Create proper refresh tokens with **7-day** expiry.
   - On every token validation, check the blacklist table. Use Redis cache (`blacklist:{jti}` with TTL matching token expiry) to avoid DB hits on every request.

3. Create `app/services/token_service.py`:
   - `blacklist_token(jti, token_type, user_id, tenant_id, expires_at)` — adds to DB + Redis.
   - `is_blacklisted(jti)` — check Redis first, fallback to DB.
   - `blacklist_all_user_tokens(user_id)` — for password change / account compromise.
   - `rotate_refresh_token(old_refresh_token)` — blacklist old, issue new pair.

4. Update `app/api/v1/auth.py`:
   - Add `POST /auth/refresh` — accepts refresh token, returns new access + refresh token (rotation).
   - Add `POST /auth/logout` — blacklists both current access and refresh tokens.
   - Update `POST /auth/change-password` in users.py — blacklists all existing tokens for the user.

5. Alembic migration for `blacklisted_tokens` table.

6. Tests:
   - Token is rejected after blacklisting.
   - Refresh rotation works and old refresh token is invalidated.
   - Logout invalidates both tokens.
   - Password change invalidates all sessions.

**Acceptance criteria:** No token can be used after logout or password change. Refresh tokens rotate on every use. Redis-backed check adds < 1ms latency.

---

### 1.2 Expired Token Cleanup Job

**Problem:** Expired tokens (password reset, email verification, API keys, blacklisted JWTs) accumulate in the database forever.

**Implementation:**

1. Create `app/services/cleanup_service.py`:
   ```python
   def cleanup_expired_tokens(db: Session) -> dict:
       """Remove all expired tokens and return counts."""
       now = datetime.utcnow()
       counts = {}

       # Expired password reset tokens
       result = db.query(PasswordResetToken).filter(PasswordResetToken.expires_at < now).delete()
       counts["password_reset_tokens"] = result

       # Expired email verification tokens
       result = db.query(EmailVerificationToken).filter(EmailVerificationToken.expires_at < now).delete()
       counts["email_verification_tokens"] = result

       # Expired blacklisted tokens (already expired, safe to remove)
       result = db.query(BlacklistedToken).filter(BlacklistedToken.expires_at < now).delete()
       counts["blacklisted_tokens"] = result

       # Expired API keys
       result = db.query(APIKey).filter(
           APIKey.expires_at.isnot(None),
           APIKey.expires_at < now,
           APIKey.is_active == False
       ).delete()
       counts["expired_api_keys"] = result

       # Old login attempts (older than 24 hours, not currently locked)
       cutoff = now - timedelta(hours=24)
       result = db.query(LoginAttempt).filter(
           LoginAttempt.locked_until < now,
           LoginAttempt.last_failed_at < cutoff
       ).delete()
       counts["old_login_attempts"] = result

       db.commit()
       return counts
   ```

2. Add Celery periodic task in `app/worker.py`:
   ```python
   from celery.schedules import crontab

   app.conf.beat_schedule = {
       "cleanup-expired-tokens": {
           "task": "app.worker.cleanup_expired_tokens_task",
           "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
       },
   }
   ```

3. Add admin endpoint `POST /admin/cleanup` (admin-only) for manual trigger.

4. Tests: Create expired tokens, run cleanup, verify they're gone. Verify non-expired tokens are untouched.

---

### 1.3 Per-API-Key Rate Limiting

**Problem:** Rate limiting is only per-IP. An API key could be abused from distributed IPs.

**Implementation:**

1. Update `app/utils/rate_limit.py`:
   - Create a custom key function that uses API key prefix (if present) OR IP as the rate limit key.
   ```python
   def get_rate_limit_key(request: Request) -> str:
       api_key = request.headers.get("X-API-Key")
       if api_key:
           return f"apikey:{api_key[:12]}"  # Use prefix
       return f"ip:{request.client.host}"
   ```

2. Add per-key rate limit configuration to `TenantSettings`:
   - `api_key_rate_limit_per_minute` (default: 60)

3. Tests: Verify rate limiting works per API key, not just per IP.

---

### 1.4 Input Sanitization for Chat Content

**Problem:** Chat messages are stored raw — potential XSS if rendered without sanitization.

**Implementation:**

1. Add `bleach` to requirements.txt.
2. Create `app/utils/sanitize.py`:
   ```python
   import bleach

   def sanitize_html(text: str) -> str:
       """Strip all HTML tags from user input."""
       return bleach.clean(text, tags=[], strip=True)

   def sanitize_chat_message(content: str) -> str:
       """Sanitize chat message content."""
       content = sanitize_html(content)
       content = content.strip()
       if len(content) > 10000:  # Max message length
           raise ValueError("Message too long")
       return content
   ```

3. Apply sanitization in `app/services/chat_service.py` before storing any user message.
4. Apply sanitization in `app/api/v1/chat.py` WebSocket handler.
5. Add Pydantic validator on chat schemas for max length.
6. Tests: HTML tags stripped, oversized messages rejected, normal text passes through unchanged.

---

## PHASE 2 — Observability & Monitoring (HIGH PRIORITY)

### 2.1 Custom Prometheus Metrics

**Problem:** Only default FastAPI metrics exist. No business-level observability.

**Implementation:**

1. Create `app/utils/metrics.py`:
   ```python
   from prometheus_client import Counter, Histogram, Gauge

   # Document processing
   DOCUMENTS_PROCESSED_TOTAL = Counter(
       "rag_documents_processed_total",
       "Total documents processed",
       ["tenant_id", "status"]  # status: success, failure
   )
   DOCUMENT_PROCESSING_DURATION = Histogram(
       "rag_document_processing_duration_seconds",
       "Time to process a document",
       ["tenant_id"],
       buckets=[1, 5, 10, 30, 60, 120, 300]
   )

   # Chat / RAG
   CHAT_REQUESTS_TOTAL = Counter(
       "rag_chat_requests_total",
       "Total chat requests",
       ["tenant_id", "mode"]  # mode: rag, fallback
   )
   CHAT_RESPONSE_DURATION = Histogram(
       "rag_chat_response_duration_seconds",
       "Time to generate chat response",
       ["tenant_id"],
       buckets=[0.5, 1, 2, 5, 10, 30]
   )
   CHAT_CONTEXT_CHUNKS_USED = Histogram(
       "rag_chat_context_chunks_used",
       "Number of context chunks used per query",
       ["tenant_id"],
       buckets=[0, 1, 2, 3, 5, 10, 20]
   )

   # Vector store
   VECTOR_STORE_QUERY_DURATION = Histogram(
       "rag_vector_query_duration_seconds",
       "ChromaDB query duration",
       ["tenant_id"],
       buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1]
   )
   VECTOR_STORE_CACHE_HITS = Counter(
       "rag_vector_cache_hits_total",
       "Vector store cache hits",
       ["tenant_id"]
   )
   VECTOR_STORE_CACHE_MISSES = Counter(
       "rag_vector_cache_misses_total",
       "Vector store cache misses",
       ["tenant_id"]
   )

   # Embeddings
   EMBEDDINGS_TOTAL = Counter(
       "rag_embeddings_created_total",
       "Total embeddings created",
       ["tenant_id"]
   )
   TOTAL_CHUNKS_STORED = Gauge(
       "rag_chunks_stored_total",
       "Total document chunks in vector store",
       ["tenant_id"]
   )

   # Auth
   AUTH_LOGIN_ATTEMPTS = Counter(
       "rag_auth_login_attempts_total",
       "Login attempts",
       ["status"]  # success, failed, locked
   )
   ACTIVE_WEBSOCKET_CONNECTIONS = Gauge(
       "rag_active_websocket_connections",
       "Currently active WebSocket connections"
   )

   # Tenants
   ACTIVE_TENANTS = Gauge(
       "rag_active_tenants_total",
       "Number of active tenants"
   )
   STORAGE_USED_BYTES = Gauge(
       "rag_storage_used_bytes",
       "Storage used in bytes",
       ["tenant_id"]
   )
   ```

2. Instrument the services:
   - `processing_service.py` → `DOCUMENTS_PROCESSED_TOTAL`, `DOCUMENT_PROCESSING_DURATION`
   - `chat_service.py` → `CHAT_REQUESTS_TOTAL`, `CHAT_RESPONSE_DURATION`, `CHAT_CONTEXT_CHUNKS_USED`
   - `vector_store.py` → `VECTOR_STORE_QUERY_DURATION`, `VECTOR_STORE_CACHE_HITS/MISSES`
   - `auth_service.py` → `AUTH_LOGIN_ATTEMPTS`
   - WebSocket handler → `ACTIVE_WEBSOCKET_CONNECTIONS`

3. Tests: Verify metrics increment correctly after operations.

---

### 2.2 Prometheus Alerting Rules

**Problem:** No alerts — issues go unnoticed until users complain.

**Implementation:**

1. Create `monitoring/prometheus/alerts.yml`:
   ```yaml
   groups:
     - name: rag-system-alerts
       rules:
         # High error rate
         - alert: HighErrorRate
           expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
           for: 5m
           labels:
             severity: critical
           annotations:
             summary: "High 5xx error rate ({{ $value | humanizePercentage }})"

         # Slow API responses
         - alert: SlowAPIResponses
           expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
           for: 10m
           labels:
             severity: warning
           annotations:
             summary: "95th percentile API latency above 5s"

         # Document processing failures
         - alert: DocumentProcessingFailures
           expr: rate(rag_documents_processed_total{status="failure"}[15m]) > 0.1
           for: 10m
           labels:
             severity: warning
           annotations:
             summary: "Document processing failure rate elevated"

         # High chat latency
         - alert: HighChatLatency
           expr: histogram_quantile(0.95, rate(rag_chat_response_duration_seconds_bucket[5m])) > 10
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "Chat response time (p95) above 10 seconds"

         # Service down
         - alert: ServiceDown
           expr: up{job="rag-api"} == 0
           for: 1m
           labels:
             severity: critical
           annotations:
             summary: "RAG API service is down"

         # Database connection issues
         - alert: DatabaseConnectionErrors
           expr: rate(sqlalchemy_pool_checkedout[5m]) > rate(sqlalchemy_pool_size[5m]) * 0.9
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "Database connection pool near exhaustion"

         # High memory usage
         - alert: HighMemoryUsage
           expr: process_resident_memory_bytes / 1024 / 1024 > 512
           for: 10m
           labels:
             severity: warning
           annotations:
             summary: "Application memory usage above 512MB"

         # Celery queue backing up
         - alert: CeleryQueueBacklog
           expr: celery_active_tasks > 50
           for: 15m
           labels:
             severity: warning
           annotations:
             summary: "Celery task queue has large backlog"
   ```

2. Update `monitoring/prometheus/prometheus.yml` to load the alert rules file.

3. Add Alertmanager configuration for notification routing (Slack/email/PagerDuty).

---

### 2.3 OpenTelemetry Distributed Tracing

**Problem:** Only request IDs exist. Cannot trace a request across API → Celery worker → ChromaDB → OpenAI.

**Implementation:**

1. Add dependencies: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-sqlalchemy`, `opentelemetry-instrumentation-redis`, `opentelemetry-instrumentation-celery`, `opentelemetry-exporter-otlp`.

2. Create `app/utils/tracing.py`:
   ```python
   from opentelemetry import trace
   from opentelemetry.sdk.trace import TracerProvider
   from opentelemetry.sdk.trace.export import BatchSpanProcessor
   from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
   from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
   from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
   from opentelemetry.instrumentation.redis import RedisInstrumentor
   from opentelemetry.instrumentation.celery import CeleryInstrumentor

   def setup_tracing(app, engine):
       if not settings.OTEL_EXPORTER_ENDPOINT:
           return

       provider = TracerProvider(resource=Resource.create({
           "service.name": "rag-api",
           "service.version": "0.6.0",
           "deployment.environment": settings.ENVIRONMENT,
       }))

       exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)
       provider.add_span_processor(BatchSpanProcessor(exporter))
       trace.set_tracer_provider(provider)

       FastAPIInstrumentor.instrument_app(app)
       SQLAlchemyInstrumentor().instrument(engine=engine)
       RedisInstrumentor().instrument()
       CeleryInstrumentor().instrument()
   ```

3. Add custom spans for:
   - Document text extraction
   - Chunking
   - ChromaDB queries
   - OpenAI API calls
   - Chat response assembly

4. Add `OTEL_EXPORTER_ENDPOINT` to config.py and .env.example.

5. Add Jaeger or Tempo to docker-compose.monitoring.yml for trace visualization.

---

## PHASE 3 — Infrastructure Hardening (HIGH PRIORITY)

### 3.1 Kubernetes Network Policies

**Problem:** All pods can communicate with all other pods. No network segmentation.

**Implementation:**

Create `k8s/network-policies.yml`:
```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: rag-system
spec:
  podSelector: {}
  policyTypes:
    - Ingress

---
# Allow ingress to API only from ingress controller
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-ingress
  namespace: rag-system
spec:
  podSelector:
    matchLabels:
      app: rag-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - port: 8000

---
# Allow API → Redis
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-redis-from-api
  namespace: rag-system
spec:
  podSelector:
    matchLabels:
      app: redis
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: rag-api
        - podSelector:
            matchLabels:
              app: rag-worker
      ports:
        - port: 6379

---
# Allow API & Worker → PostgreSQL
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-postgres-from-app
  namespace: rag-system
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: rag-api
        - podSelector:
            matchLabels:
              app: rag-worker
      ports:
        - port: 5432
```

---

### 3.2 PodDisruptionBudget

Create `k8s/pdb.yml`:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: rag-api-pdb
  namespace: rag-system
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: rag-api
```

---

### 3.3 Sealed Secrets

**Problem:** K8s secrets are base64-encoded plaintext in the repo.

**Implementation:**

1. Add Bitnami Sealed Secrets controller to the cluster.
2. Create `k8s/sealed-secret.yml` using `kubeseal` CLI.
3. Add instructions in README for secret management workflow.
4. Remove plaintext secret values from `k8s/secret.yml`, replace with sealed secret references.

---

### 3.4 PostgreSQL StatefulSet for Kubernetes

**Problem:** No database deployment in K8s manifests.

**Implementation:**

Create `k8s/postgres-statefulset.yml`:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: rag-system
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: rag-secrets
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: rag-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: rag-secrets
                  key: POSTGRES_PASSWORD
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "$(POSTGRES_USER)"]
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "$(POSTGRES_USER)"]
            initialDelaySeconds: 5
            periodSeconds: 5
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 20Gi
```

Add corresponding Service manifest.

---

## PHASE 4 — Testing & Quality (MEDIUM PRIORITY)

### 4.1 Integration Tests with PostgreSQL

**Problem:** All tests run against SQLite, which has different behavior from PostgreSQL (e.g., no real UUID type, no array type, different locking).

**Implementation:**

1. Add `testcontainers` to dev dependencies.
2. Create `tests/integration/conftest.py`:
   ```python
   import pytest
   from testcontainers.postgres import PostgresContainer

   @pytest.fixture(scope="session")
   def postgres_container():
       with PostgresContainer("postgres:15") as pg:
           yield pg

   @pytest.fixture(scope="function")
   def pg_db(postgres_container):
       engine = create_engine(postgres_container.get_connection_url())
       Base.metadata.create_all(engine)
       Session = sessionmaker(bind=engine)
       session = Session()
       yield session
       session.close()
       Base.metadata.drop_all(engine)
   ```

3. Create integration test suite under `tests/integration/`:
   - `test_tenant_isolation_pg.py` — verify tenant isolation with real PostgreSQL constraints.
   - `test_concurrent_access.py` — test concurrent document uploads, chat messages.
   - `test_migration_roundtrip.py` — run all migrations up, then down, then up again.
   - `test_cascade_deletes.py` — verify cascade behavior with real foreign keys.

4. Update CI pipeline:
   ```yaml
   integration-test:
     runs-on: ubuntu-latest
     services:
       postgres:
         image: postgres:15
         env:
           POSTGRES_PASSWORD: test
         options: >-
           --health-cmd pg_isready
           --health-interval 10s
           --health-timeout 5s
           --health-retries 5
     steps:
       - run: pytest tests/integration/ -v
   ```

---

### 4.2 Coverage Threshold in CI

Update `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"
```

Update CI to fail if coverage drops below 80%.

---

### 4.3 Migration Round-Trip Tests

```python
def test_migration_roundtrip(pg_db):
    """Verify all migrations can go up and down cleanly."""
    alembic_cfg = Config("alembic.ini")
    # Upgrade to head
    command.upgrade(alembic_cfg, "head")
    # Downgrade to base
    command.downgrade(alembic_cfg, "base")
    # Upgrade again
    command.upgrade(alembic_cfg, "head")
```

---

## PHASE 5 — API Maturity & Features (MEDIUM PRIORITY)

### 5.1 Soft Delete

**Problem:** Hard deletes lose data permanently. No way to recover accidentally deleted documents or users.

**Implementation:**

1. Create a mixin:
   ```python
   class SoftDeleteMixin:
       deleted_at = Column(DateTime, nullable=True, default=None, index=True)
       deleted_by_id = Column(UUID, nullable=True)

       @hybrid_property
       def is_deleted(self):
           return self.deleted_at is not None
   ```

2. Apply to `Document`, `User`, `ChatMessage` models.

3. Add `@event.listens_for(Session, "do_orm_execute")` to automatically filter out soft-deleted records unless explicitly requested.

4. Add `include_deleted` query parameter to list endpoints (admin only).

5. Add `POST /documents/{id}/restore` and `POST /users/{id}/restore` endpoints (admin only).

6. Add cleanup job: permanently delete soft-deleted records after 30 days.

7. Alembic migration for `deleted_at` and `deleted_by_id` columns.

---

### 5.2 Document Re-Processing

**Problem:** If chunking strategy or embedding model changes, no way to re-process existing documents.

**Implementation:**

1. Add `POST /documents/{id}/reprocess` endpoint:
   - Deletes existing chunks from DB and ChromaDB.
   - Re-runs the processing pipeline.
   - Only available for documents with status COMPLETED or FAILED.

2. Add `POST /documents/reprocess-all` (admin only):
   - Queues all tenant documents for re-processing via Celery.
   - Returns a batch job ID for tracking.

3. Add `processing_version` column to Document model to track which version of the pipeline processed it.

---

### 5.3 Bulk Document Upload

**Implementation:**

1. Add `POST /documents/bulk` endpoint:
   - Accepts multipart form with multiple files.
   - Validates all files first (type, size, quota), then processes.
   - Returns list of created document IDs.
   - Queues all for processing via Celery.

2. Add quota check for total batch size.

3. Tests: Upload 5 files at once, verify all are created and queued.

---

### 5.4 Webhook System for Events

**Problem:** External systems can't react to events (document processed, subscription changed).

**Implementation:**

1. Create models:
   ```python
   class WebhookEndpoint(Base):
       __tablename__ = "webhook_endpoints"
       id = Column(UUID, primary_key=True)
       tenant_id = Column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"))
       url = Column(String, nullable=False)
       secret = Column(String, nullable=False)  # For HMAC signing
       events = Column(JSON, nullable=False)  # ["document.processed", "subscription.changed"]
       is_active = Column(Boolean, default=True)
       created_at = Column(DateTime, default=func.now())

   class WebhookDelivery(Base):
       __tablename__ = "webhook_deliveries"
       id = Column(UUID, primary_key=True)
       webhook_id = Column(UUID, ForeignKey("webhook_endpoints.id", ondelete="CASCADE"))
       event_type = Column(String, nullable=False)
       payload = Column(JSON, nullable=False)
       response_status = Column(Integer, nullable=True)
       attempt_count = Column(Integer, default=0)
       delivered_at = Column(DateTime, nullable=True)
       next_retry_at = Column(DateTime, nullable=True)
   ```

2. Create `app/services/webhook_service.py`:
   - `dispatch_event(tenant_id, event_type, payload)` — finds matching webhooks, queues deliveries.
   - `deliver_webhook(delivery_id)` — Celery task, HMAC-signed payload, retry with exponential backoff (3 attempts).
   - Events: `document.uploaded`, `document.processed`, `document.failed`, `document.deleted`, `user.invited`, `user.deleted`, `subscription.changed`, `quota.warning` (80% usage).

3. API endpoints:
   - `POST /webhooks` — register endpoint.
   - `GET /webhooks` — list endpoints.
   - `DELETE /webhooks/{id}` — remove endpoint.
   - `GET /webhooks/{id}/deliveries` — delivery history.
   - `POST /webhooks/{id}/test` — send test event.

4. Alembic migration.

---

### 5.5 Pagination on Chat Conversations

**Problem:** Chat conversations list has no pagination.

**Implementation:**

1. Add `skip` and `limit` query params to `GET /chat/conversations`.
2. Add total count in response header (`X-Total-Count`).
3. Update schema to include pagination metadata.

---

## PHASE 6 — Data & Performance (MEDIUM PRIORITY)

### 6.1 Redis Caching Layer

**Problem:** No caching for frequently accessed data (tenant settings, user profiles, dashboard stats).

**Implementation:**

1. Create `app/services/cache_service.py`:
   ```python
   class CacheService:
       def __init__(self, redis_client):
           self.redis = redis_client
           self.default_ttl = 300  # 5 minutes

       async def get_or_set(self, key: str, factory: Callable, ttl: int = None):
           cached = await self.redis.get(key)
           if cached:
               return json.loads(cached)
           value = await factory()
           await self.redis.setex(key, ttl or self.default_ttl, json.dumps(value, default=str))
           return value

       async def invalidate(self, pattern: str):
           keys = await self.redis.keys(pattern)
           if keys:
               await self.redis.delete(*keys)
   ```

2. Cache these with automatic invalidation:
   - Tenant settings → invalidate on settings update.
   - Dashboard stats → 5 min TTL, invalidate on document upload/delete.
   - User profile → invalidate on user update.
   - Document list → invalidate on upload/delete.

3. Add cache hit/miss metrics to Prometheus.

---

### 6.2 ChromaDB Production Mode

**Problem:** ChromaDB runs embedded. Not suitable for production at scale.

**Implementation:**

1. Add ChromaDB server to docker-compose.yml:
   ```yaml
   chromadb:
     image: chromadb/chroma:latest
     ports:
       - "8001:8000"
     volumes:
       - chroma_data:/chroma/chroma
     environment:
       - CHROMA_SERVER_AUTH_CREDENTIALS=your-token
       - CHROMA_SERVER_AUTH_PROVIDER=chromadb.auth.token.TokenAuthServerProvider
   ```

2. Update `app/services/vector_store.py` to support both modes:
   ```python
   if settings.CHROMA_HOST:
       client = chromadb.HttpClient(
           host=settings.CHROMA_HOST,
           port=settings.CHROMA_PORT,
           headers={"Authorization": f"Bearer {settings.CHROMA_TOKEN}"}
       )
   else:
       client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
   ```

3. Add `CHROMA_HOST`, `CHROMA_PORT`, `CHROMA_TOKEN` to config.py and .env.example.

4. Add K8s manifest for ChromaDB StatefulSet.

---

## PHASE 7 — Documentation (LOW PRIORITY)

### 7.1 Architecture Diagram

Create `docs/architecture.md` with a C4 context and container diagram (use Mermaid syntax for rendering in GitHub):
- System context: Users, External APIs (OpenAI, Stripe, SMTP)
- Container: FastAPI API, Celery Worker, PostgreSQL, Redis, ChromaDB, S3
- Show data flow for key operations: document upload, RAG chat query

### 7.2 Incident Runbook

Create `docs/runbook.md` covering:
- ChromaDB is down / corrupted → how to rebuild from document chunks
- PostgreSQL connection pool exhaustion → diagnosis and recovery
- Celery workers stuck → how to purge queue and restart
- OpenAI API outage → fallback mode behavior
- High memory usage → profiling steps
- Failed migration → rollback procedure
- Tenant data corruption → isolation verification steps

### 7.3 API Changelog

Create `docs/CHANGELOG.md` following Keep a Changelog format. Document all API changes starting from v0.5.0.

### 7.4 Contributing Guide

Create `CONTRIBUTING.md` with:
- Development setup (Python 3.12+, Docker, .env)
- Running tests locally
- Migration workflow
- PR conventions
- Code style (ruff config)

---

## PHASE 8 — Frontend Improvements (LOW PRIORITY)

### 8.1 Error Handling UI

1. Add a toast notification system (`frontend/js/toast.js`).
2. Wrap all API calls with error handling that shows user-friendly messages.
3. Add loading states for async operations.
4. Add offline detection and reconnection for WebSocket.

### 8.2 Frontend Tests

1. Add Playwright for E2E tests:
   - Register → Login → Upload Document → Chat flow.
   - Admin: manage users, view audit logs, update settings.
   - Error states: invalid login, file too large, rate limited.

2. Add to CI pipeline.

---

## Summary — Execution Order

| Phase | Priority | Effort | Impact |
|-------|----------|--------|--------|
| 1. Security Hardening | HIGH | 2-3 days | Blocks production deployment |
| 2. Observability | HIGH | 1-2 days | Critical for operations |
| 3. Infrastructure | HIGH | 1-2 days | Required for K8s production |
| 4. Testing | MEDIUM | 2-3 days | Confidence in correctness |
| 5. API Maturity | MEDIUM | 3-4 days | Feature completeness |
| 6. Data & Performance | MEDIUM | 1-2 days | Scalability |
| 7. Documentation | LOW | 1 day | Team productivity |
| 8. Frontend | LOW | 2-3 days | User experience |

**Total estimated effort: 13-20 days of focused work.**

Start with Phase 1 (Security) — nothing else matters if tokens can't be revoked and expired data piles up. Then Phase 2 (Observability) so you can actually see what's happening in production. Phase 3 (Infrastructure) before any real K8s deployment. The rest follows naturally.
