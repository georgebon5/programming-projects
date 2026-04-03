"""
Custom Prometheus business-level metrics for the Multi-Tenant AI RAG System.
"""

from prometheus_client import Counter, Gauge, Histogram

# ── Document Processing ──────────────────────────────────────────────────────
DOCUMENTS_PROCESSED_TOTAL = Counter(
    "rag_documents_processed_total",
    "Total documents processed",
    ["status"],  # "success" or "failure"
)
DOCUMENT_PROCESSING_DURATION = Histogram(
    "rag_document_processing_duration_seconds",
    "Time to process a document end-to-end",
    buckets=[1, 5, 10, 30, 60, 120, 300],
)
DOCUMENT_CHUNKS_CREATED = Counter(
    "rag_document_chunks_created_total",
    "Total document chunks created",
)

# ── Chat / RAG ───────────────────────────────────────────────────────────────
CHAT_REQUESTS_TOTAL = Counter(
    "rag_chat_requests_total",
    "Total chat requests",
    ["mode"],  # "rag" or "fallback"
)
CHAT_RESPONSE_DURATION = Histogram(
    "rag_chat_response_duration_seconds",
    "Time to generate a chat response",
    buckets=[0.5, 1, 2, 5, 10, 30],
)
CHAT_CONTEXT_CHUNKS_USED = Histogram(
    "rag_chat_context_chunks_used",
    "Number of context chunks retrieved per chat query",
    buckets=[0, 1, 2, 3, 5, 10, 20],
)

# ── Vector Store ─────────────────────────────────────────────────────────────
VECTOR_STORE_QUERY_DURATION = Histogram(
    "rag_vector_query_duration_seconds",
    "ChromaDB query duration",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1],
)
VECTOR_CACHE_HITS = Counter(
    "rag_vector_cache_hits_total",
    "Vector store cache hits",
)
VECTOR_CACHE_MISSES = Counter(
    "rag_vector_cache_misses_total",
    "Vector store cache misses",
)

# ── Auth ─────────────────────────────────────────────────────────────────────
AUTH_LOGIN_ATTEMPTS = Counter(
    "rag_auth_login_attempts_total",
    "Login attempts",
    ["status"],  # "success", "failed", "locked"
)
AUTH_REGISTRATIONS = Counter(
    "rag_auth_registrations_total",
    "New tenant registrations",
)

# ── WebSocket ────────────────────────────────────────────────────────────────
ACTIVE_WEBSOCKET_CONNECTIONS = Gauge(
    "rag_active_websocket_connections",
    "Currently active WebSocket connections",
)

# ── Redis Cache ───────────────────────────────────────────────────────────────
CACHE_HITS = Counter("app_cache_hits_total", "Redis cache hits")
CACHE_MISSES = Counter("app_cache_misses_total", "Redis cache misses")
