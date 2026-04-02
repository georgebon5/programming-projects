"""
ChromaDB vector store wrapper with tenant isolation.
Each tenant gets its own ChromaDB collection.
Includes TTL-based caching for search results.
"""

import hashlib
import logging
import threading
import time
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.utils.metrics import VECTOR_CACHE_HITS, VECTOR_CACHE_MISSES, VECTOR_STORE_QUERY_DURATION
from app.utils.tracing import trace_span

logger = logging.getLogger(__name__)

# ── Search result cache (TTL 5 minutes, max 256 entries) ────────────────
# Cache value: (timestamp, tenant_id_str, results)
_cache: dict[str, tuple[float, str, list[dict]]] = {}
_cache_lock = threading.Lock()
_CACHE_TTL_SECONDS = 300
_CACHE_MAX_SIZE = 256


def _get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=settings.vector_db_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _collection_name(tenant_id: UUID) -> str:
    """One collection per tenant for strict isolation."""
    return f"tenant_{tenant_id}"


def store_chunks(
    tenant_id: UUID,
    document_id: UUID,
    chunks: list[str],
) -> list[str]:
    """
    Store text chunks in ChromaDB for a specific tenant.
    ChromaDB generates embeddings automatically using its default model.

    Returns the list of embedding IDs (one per chunk).
    """
    client = _get_client()
    collection = client.get_or_create_collection(
        name=_collection_name(tenant_id),
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=[
            {
                "document_id": str(document_id),
                "tenant_id": str(tenant_id),
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ],
    )

    # Invalidate search cache since new data was added
    invalidate_cache(tenant_id)

    return ids


def _cache_key(tenant_id: UUID, query: str, n_results: int, document_id: UUID | None) -> str:
    """Generate a deterministic cache key for search parameters."""
    raw = f"{tenant_id}:{query}:{n_results}:{document_id or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> list[dict] | None:
    """Get cached value if still within TTL."""
    import time

    with _cache_lock:
        if key in _cache:
            ts, _tenant, value = _cache[key]
            if time.time() - ts < _CACHE_TTL_SECONDS:
                logger.debug("Cache hit for search key %s", key[:12])
                return value
            del _cache[key]
    return None


def _cache_set(key: str, tenant_id: UUID, value: list[dict]) -> None:
    """Store value in cache with current timestamp and tenant_id for scoped invalidation."""
    import time

    with _cache_lock:
        # Evict oldest if at capacity
        if len(_cache) >= _CACHE_MAX_SIZE and key not in _cache:
            oldest_key = min(_cache, key=lambda k: _cache[k][0])
            del _cache[oldest_key]
        _cache[key] = (time.time(), str(tenant_id), value)


def invalidate_cache(tenant_id: UUID, document_id: UUID | None = None) -> None:
    """Invalidate cached search results for a specific tenant only."""
    tenant_str = str(tenant_id)
    with _cache_lock:
        keys_to_delete = [k for k, (_ts, tid, _v) in _cache.items() if tid == tenant_str]
        for k in keys_to_delete:
            del _cache[k]
    logger.debug(
        "Search cache invalidated for tenant %s (document=%s): %d entries removed",
        tenant_str,
        document_id,
        len(keys_to_delete),
    )


def search_chunks(
    tenant_id: UUID,
    query: str,
    n_results: int = 5,
    document_id: UUID | None = None,
) -> list[dict]:
    """
    Search for relevant chunks in a tenant's collection.
    Results are cached with a TTL to reduce redundant vector lookups.

    Returns list of dicts with keys: text, document_id, chunk_index, distance.
    """
    # Check cache first
    key = _cache_key(tenant_id, query, n_results, document_id)
    cached = _cache_get(key)
    if cached is not None:
        VECTOR_CACHE_HITS.inc()
        return cached

    VECTOR_CACHE_MISSES.inc()

    client = _get_client()

    try:
        collection = client.get_collection(name=_collection_name(tenant_id))
    except Exception as exc:
        logger.debug("No vector collection found for tenant %s: %s", tenant_id, exc)
        return []

    where_filter = None
    if document_id:
        where_filter = {"document_id": str(document_id)}

    with trace_span("vector_store.search", {"tenant.id": str(tenant_id), "n_results": n_results}) as span:
        _query_start = time.time()
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
        VECTOR_STORE_QUERY_DURATION.observe(time.time() - _query_start)

        items: list[dict] = []
        if results["documents"] and results["documents"][0]:
            for i, doc_text in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else None
                items.append({
                    "text": doc_text,
                    "document_id": meta.get("document_id"),
                    "chunk_index": meta.get("chunk_index"),
                    "distance": distance,
                })

        if span:
            span.set_attribute("vector_store.results_count", len(items))

    # Store in cache
    _cache_set(key, tenant_id, items)

    return items


def delete_document_chunks(tenant_id: UUID, document_id: UUID) -> None:
    """Delete all chunks for a document from ChromaDB."""
    client = _get_client()
    try:
        collection = client.get_collection(name=_collection_name(tenant_id))
        collection.delete(where={"document_id": str(document_id)})
        invalidate_cache(tenant_id, document_id)
    except Exception as exc:
        logger.warning(
            "Failed to delete chunks for document %s (tenant %s): %s",
            document_id,
            tenant_id,
            exc,
        )
