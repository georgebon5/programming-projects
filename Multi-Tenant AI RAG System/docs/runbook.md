# Incident Runbook — Multi-Tenant AI RAG System

> Last updated: 2026-04-03
> Stack: FastAPI · PostgreSQL · Redis · ChromaDB · Celery · OpenAI API · S3/Local Storage · Prometheus/Grafana

---

## Table of Contents

1. [ChromaDB Down / Corrupted](#1-chromadb-down--corrupted)
2. [PostgreSQL Connection Pool Exhaustion](#2-postgresql-connection-pool-exhaustion)
3. [Celery Workers Stuck](#3-celery-workers-stuck)
4. [OpenAI API Outage](#4-openai-api-outage)
5. [High Memory Usage](#5-high-memory-usage)
6. [Failed Alembic Migration](#6-failed-alembic-migration)
7. [Tenant Data Corruption / Isolation Breach](#7-tenant-data-corruption--isolation-breach)
8. [Redis Down](#8-redis-down)
9. [Token / Authentication Issues](#9-token--authentication-issues)

---

## 1. ChromaDB Down / Corrupted

### Symptoms
- Chat queries return empty results or zero-length answer arrays
- HTTP 500 errors on `POST /api/v1/chat/`
- App logs contain `chromadb`, `Connection refused`, or `Collection not found` errors

### Diagnosis

**Kubernetes**
```bash
# Check pod status
kubectl get pods -n <namespace> -l app=chromadb

# Tail logs
kubectl logs -n <namespace> deploy/chromadb --tail=100

# Exec into the app pod and probe the HTTP endpoint
kubectl exec -it deploy/api -n <namespace> -- \
  curl -sf http://$CHROMA_HOST:8000/api/v1/heartbeat
```

**Docker Compose**
```bash
docker compose ps chromadb
docker compose logs --tail=100 chromadb

# HTTP mode connectivity check
curl -sf http://localhost:8000/api/v1/heartbeat
```

**Token auth (HTTP mode)**
```bash
curl -H "Authorization: Bearer $CHROMA_TOKEN" \
  http://$CHROMA_HOST:8000/api/v1/collections
```

### Recovery Steps

1. **Restart the service**
   ```bash
   # Kubernetes
   kubectl rollout restart deploy/chromadb -n <namespace>

   # Docker Compose
   docker compose restart chromadb
   ```

2. **Verify heartbeat** before continuing.

3. **Rebuild all vector collections from PostgreSQL chunks**
   ```bash
   curl -X POST http://localhost:8000/api/v1/documents/reprocess-all \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```
   This re-embeds all document chunks stored in PostgreSQL and repopulates ChromaDB. Monitor Celery task progress via logs or Flower.

4. **If data directory is corrupted** (embedded mode), wipe and rebuild:
   ```bash
   docker compose stop chromadb
   docker volume rm <chromadb_volume>
   docker compose up -d chromadb
   # Then re-run reprocess-all above
   ```

### Prevention
- Use ChromaDB in HTTP mode in production to isolate memory and allow independent restarts.
- Include a ChromaDB readiness probe in Kubernetes liveness/readiness checks.
- Regularly snapshot the ChromaDB volume or rely on PostgreSQL as the source of truth for re-embedding.

---

## 2. PostgreSQL Connection Pool Exhaustion

### Symptoms
- HTTP 500 errors across multiple endpoints
- App or worker logs show `too many connections` or `FATAL: remaining connection slots are reserved`
- New requests queue and eventually time out

### Diagnosis

```bash
# Check active connections grouped by state and application
psql $DATABASE_URL -c "
  SELECT state, application_name, count(*)
  FROM pg_stat_activity
  GROUP BY state, application_name
  ORDER BY count DESC;"

# Identify long-running queries (> 30 s)
psql $DATABASE_URL -c "
  SELECT pid, now() - query_start AS duration, state, query
  FROM pg_stat_activity
  WHERE state != 'idle'
    AND query_start < now() - interval '30 seconds'
  ORDER BY duration DESC;"

# Check configured max_connections
psql $DATABASE_URL -c "SHOW max_connections;"

# SQLAlchemy pool status — check app /metrics endpoint
curl -s http://localhost:8000/metrics | grep sqlalchemy
```

### Recovery Steps

1. **Kill idle-in-transaction or long-running connections** if safe:
   ```bash
   psql $DATABASE_URL -c "
     SELECT pg_terminate_backend(pid)
     FROM pg_stat_activity
     WHERE state = 'idle in transaction'
       AND query_start < now() - interval '5 minutes';"
   ```

2. **Restart app pods / workers** to reset their connection pools:
   ```bash
   kubectl rollout restart deploy/api deploy/celery-worker -n <namespace>
   # or
   docker compose restart api celery_worker
   ```

3. **Increase pool size** (requires config change and redeploy):
   - Raise `SQLALCHEMY_POOL_SIZE` and `SQLALCHEMY_MAX_OVERFLOW` environment variables.
   - Alternatively, deploy PgBouncer as a connection pooler in front of PostgreSQL.

4. **Tune PostgreSQL** `max_connections` if headroom is permanently insufficient.

### Prevention
- Set `pool_pre_ping=True` in SQLAlchemy to recycle stale connections.
- Monitor `pg_stat_activity` via Prometheus `postgres_exporter`.
- Alert when active connections exceed 80% of `max_connections`.

---

## 3. Celery Workers Stuck

### Symptoms
- Documents remain in `processing` status indefinitely
- Task queue depth grows in Redis
- No recent task completions in Flower or worker logs

### Diagnosis

```bash
# List active tasks on all workers
celery -A app.celery inspect active

# List reserved (queued) tasks
celery -A app.celery inspect reserved

# Check worker logs
kubectl logs -n <namespace> deploy/celery-worker --tail=200
# or
docker compose logs --tail=200 celery_worker

# Verify Redis broker is reachable from a worker pod
kubectl exec -it deploy/celery-worker -n <namespace> -- \
  redis-cli -u $REDIS_URL ping
```

### Recovery Steps

1. **Restart workers** to release stuck tasks:
   ```bash
   kubectl rollout restart deploy/celery-worker -n <namespace>
   # or
   docker compose restart celery_worker
   ```

2. **Purge the task queue** if tasks are poisoned / unretriable:
   ```bash
   celery -A app.celery purge -f
   ```
   > Warning: this discards all queued tasks. Only do this if reprocessing via the API is preferable.

3. **Reprocess stuck documents** after workers are healthy:
   ```bash
   # Reprocess all documents still in 'processing' state
   curl -X POST http://localhost:8000/api/v1/documents/reprocess-all \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

4. **Check for Redis connectivity issues** — if Redis is intermittently unavailable, tasks will not be acknowledged (see [Section 8](#8-redis-down)).

### Prevention
- Set task `time_limit` and `soft_time_limit` to prevent indefinitely running tasks.
- Configure `CELERY_TASK_ACKS_LATE=True` with `CELERY_WORKER_PREFETCH_MULTIPLIER=1` for at-least-once delivery.
- Alert on queue depth via Prometheus Celery metrics.

---

## 4. OpenAI API Outage

### Symptoms
- Chat requests time out or return HTTP 502/503
- Document processing tasks fail at the embedding or completion stage
- App logs contain `openai.APIError`, `RateLimitError`, or `ServiceUnavailableError`

### Diagnosis

```bash
# Check OpenAI status
open https://status.openai.com

# Scan app logs for OpenAI errors
kubectl logs deploy/api -n <namespace> | grep -i openai
kubectl logs deploy/celery-worker -n <namespace> | grep -i openai

# Confirm your API key is still valid (outside of an outage)
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.error // "OK"'
```

### Impact
- `POST /api/v1/chat/` — unavailable; returns error to users.
- Document upload pipeline — uploads succeed, but embedding tasks fail and are retried by Celery.
- Existing indexed documents are unaffected once the outage clears.

### Mitigation

1. **Celery retries automatically** — embedding tasks use exponential back-off and will retry when the API recovers. No manual action is required for documents already in the queue.

2. **Communicate status** to users; surface the outage via your own status page.

3. **Do not purge the Celery queue** during an OpenAI outage — tasks will self-heal.

4. **Post-recovery** — verify all documents that were in `processing` state have transitioned to `completed`:
   ```bash
   psql $DATABASE_URL -c "
     SELECT status, count(*) FROM documents GROUP BY status;"
   ```
   If any remain stuck, run reprocess-all (see Section 3, step 3).

### Prevention
- Configure `max_retries` and `retry_backoff` on embedding/completion Celery tasks.
- Add an OpenAI API health check to your Grafana dashboard (synthetic probe or log-based alert).

---

## 5. High Memory Usage

### Symptoms
- OOMKilled pod restarts (`kubectl describe pod` shows `OOMKilled` reason)
- Grafana shows memory approaching container limits
- Application becomes sluggish before crashing

### Diagnosis

```bash
# Kubernetes — check recent OOM events
kubectl describe pods -n <namespace> | grep -A5 OOMKilled
kubectl top pods -n <namespace>

# Prometheus / Grafana
# Dashboard: Container Memory Usage — look for growth trends over hours

# App metrics endpoint
curl -s http://localhost:8000/metrics | grep -E 'process_resident|process_virtual'

# Docker Compose
docker stats --no-stream
```

**Common causes to investigate:**
- Large file uploads loaded entirely into memory before streaming to S3/storage.
- ChromaDB running in embedded mode — its in-process HNSW index grows with collection size.
- SQLAlchemy sessions not closed (connection leaks keep result sets in memory).
- Celery worker `--concurrency` set too high for the available RAM.

### Recovery Steps

1. **Restart affected pods** immediately to restore service:
   ```bash
   kubectl rollout restart deploy/api deploy/celery-worker -n <namespace>
   ```

2. **Identify the culprit** from metrics before the next incident.

3. **ChromaDB embedded mode** — migrate to HTTP mode to move vector index memory out of the app process:
   - Set `CHROMA_HOST` and `CHROMA_TOKEN` environment variables.
   - Redeploy ChromaDB as a separate service.

4. **Increase memory limits** as a short-term measure if demand is legitimate.

5. **Reduce Celery concurrency** if workers are the culprit:
   ```bash
   celery -A app.celery worker --concurrency=2
   ```

### Prevention
- Set Kubernetes resource `requests` and `limits` for all containers.
- Alert at 80% memory utilization to allow pre-emptive action.
- Stream large file uploads directly to S3 rather than buffering in memory.
- Use `expire_on_commit=False` carefully; always close sessions in `finally` blocks.

---

## 6. Failed Alembic Migration

### Symptoms
- Application fails to start with a `ProgrammingError` or `column does not exist` error.
- `alembic upgrade head` exits non-zero.
- Deployment rolls back or pods crash-loop.

### Diagnosis

```bash
# Check current revision applied to the database
alembic current

# View migration history and identify the last successful revision
alembic history --verbose

# Inspect the error in detail
alembic upgrade head 2>&1 | tail -30
```

### Recovery Steps

1. **Roll back one revision**:
   ```bash
   alembic downgrade -1
   ```
   Repeat if multiple revisions need rolling back; target a known-good revision with:
   ```bash
   alembic downgrade <revision_id>
   ```

2. **Fix the migration script** — edit the failing file in `alembic/versions/`.

3. **Test locally against a copy of the database schema** before re-deploying.

4. **Re-run the migration**:
   ```bash
   alembic upgrade head
   ```

5. **Re-deploy the application**.

### Prevention
- Run `alembic upgrade head` in CI against a test database (see `test_migrations.py`).
- Always write `downgrade()` functions that cleanly reverse the `upgrade()`.
- Never modify an already-merged migration; create a new revision instead.
- Keep migrations small and single-purpose to limit blast radius.

---

## 7. Tenant Data Corruption / Isolation Breach

### Symptoms
- A tenant reports seeing another tenant's documents or results.
- Audit logs contain cross-tenant record access.
- Integration tests in `test_tenant_isolation_pg.py` start failing.

### Diagnosis

```bash
# Review recent audit log entries for cross-tenant activity
psql $DATABASE_URL -c "
  SELECT tenant_id, actor_tenant_id, resource_type, resource_id, action, created_at
  FROM audit_logs
  WHERE tenant_id != actor_tenant_id
  ORDER BY created_at DESC
  LIMIT 50;"

# Confirm tenant_id on suspected records
psql $DATABASE_URL -c "
  SELECT id, tenant_id, created_at
  FROM documents
  WHERE id IN (<suspected_ids>);"

# Re-run isolation test suite
pytest tests/test_tenant_isolation_pg.py -v
```

### Recovery Steps

1. **Contain** — if an active breach is suspected, revoke affected tokens immediately:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/cleanup \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

2. **Identify all affected records** using the audit trail and tenant_id mismatch queries above.

3. **Restore from backup** for any records that were incorrectly written to the wrong tenant:
   ```bash
   # Point-in-time restore from pg_dump backup
   pg_restore -d $DATABASE_URL -t documents <backup_file>
   ```

4. **Verify isolation** after restore:
   ```bash
   pytest tests/test_tenant_isolation_pg.py -v
   ```

5. **Post-mortem** — determine root cause (missing `tenant_id` filter in a query, missing row-level security policy, etc.) and patch before reopening to users.

### Prevention
- Enforce PostgreSQL Row-Level Security (RLS) policies on all tenant-scoped tables.
- Run `test_tenant_isolation_pg.py` in every CI pipeline and pre-deployment check.
- Require `tenant_id` as a non-nullable foreign key on all tenant-scoped tables.
- Alert on `audit_logs` entries where `tenant_id != actor_tenant_id`.

---

## 8. Redis Down

### Symptoms
- Rate limiting is disabled (requests no longer throttled)
- Response caching is bypassed (higher latency, higher DB load)
- Celery tasks stop processing — new tasks cannot be enqueued or dequeued
- Worker logs show `redis.exceptions.ConnectionError`

### Diagnosis

```bash
# Quick connectivity check
redis-cli -u $REDIS_URL ping   # expected: PONG

# Kubernetes
kubectl get pods -n <namespace> -l app=redis
kubectl logs -n <namespace> deploy/redis --tail=100

# Docker Compose
docker compose ps redis
docker compose logs --tail=100 redis

# Check persistence configuration
redis-cli -u $REDIS_URL CONFIG GET save
redis-cli -u $REDIS_URL CONFIG GET appendonly
```

### Impact
- `CacheService` degrades gracefully — cache misses fall through to the database; no application errors.
- Rate limiting is silently bypassed — monitor for abuse during outage.
- Celery tasks are blocked — document processing halts until Redis recovers.

### Recovery Steps

1. **Restart Redis**:
   ```bash
   kubectl rollout restart deploy/redis -n <namespace>
   # or
   docker compose restart redis
   ```

2. **Verify** with `redis-cli ping` and check Celery worker logs for reconnection.

3. **Restart Celery workers** if they do not automatically reconnect:
   ```bash
   kubectl rollout restart deploy/celery-worker -n <namespace>
   ```

4. **Check data persistence** — if RDB/AOF is not configured and Redis was restarted, the task queue is empty. Reprocess any documents stuck in `processing` state:
   ```bash
   curl -X POST http://localhost:8000/api/v1/documents/reprocess-all \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

### Prevention
- Enable AOF persistence (`appendonly yes`) so the task queue survives restarts.
- Deploy Redis Sentinel or Redis Cluster for high availability in production.
- Alert on Redis connectivity failures via Prometheus `redis_up` metric.

---

## 9. Token / Authentication Issues

### Symptoms
- Users cannot log in; `POST /api/v1/auth/login` returns 401 or 500
- Valid tokens are rejected with 401 Unauthorized
- Token refresh fails

### Diagnosis

```bash
# Confirm JWT_SECRET_KEY is identical across all app pods
kubectl get pods -n <namespace> -l app=api -o name | xargs -I{} \
  kubectl exec {} -n <namespace> -- printenv JWT_SECRET_KEY | sort -u
# There must be exactly ONE unique value.

# Check the token_blacklist table for unexpected entries
psql $DATABASE_URL -c "
  SELECT count(*), max(created_at) FROM token_blacklist;"

# Check for recently revoked tokens or tokens_revoked_at timestamps
psql $DATABASE_URL -c "
  SELECT id, email, tokens_revoked_at
  FROM users
  WHERE tokens_revoked_at IS NOT NULL
  ORDER BY tokens_revoked_at DESC
  LIMIT 20;"

# Decode a suspect token to verify issuer/expiry (no secret needed)
# Install: pip install python-jose
python3 -c "
import sys
from jose import jwt
token = sys.argv[1]
print(jwt.get_unverified_claims(token))
" <TOKEN>
```

### Recovery Steps

1. **JWT_SECRET_KEY mismatch** — ensure all pods use the same Kubernetes Secret:
   ```bash
   kubectl get secret <app-secret> -n <namespace> -o jsonpath='{.data.JWT_SECRET_KEY}' | base64 -d
   # Update if wrong, then rolling-restart to pick up the new value
   kubectl rollout restart deploy/api -n <namespace>
   ```

2. **Bloated token_blacklist** causing lookup slowdowns — run the admin cleanup:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/cleanup \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

3. **tokens_revoked_at set incorrectly on a user** — reset carefully:
   ```bash
   psql $DATABASE_URL -c "
     UPDATE users SET tokens_revoked_at = NULL WHERE id = '<user_id>';"
   ```

4. **Force users to re-authenticate** after a secret key rotation by updating `JWT_SECRET_KEY` and redeploying — all existing tokens will immediately become invalid.

### Prevention
- Store `JWT_SECRET_KEY` in a Kubernetes Secret or Vault; never in environment-specific config files.
- Index the `token_blacklist` table on `(token_jti, expires_at)` and schedule periodic cleanup of expired entries.
- Alert on elevated 401 error rates via Prometheus / Grafana.
- Rotate `JWT_SECRET_KEY` on a schedule and handle the transition period with a short overlap window.
