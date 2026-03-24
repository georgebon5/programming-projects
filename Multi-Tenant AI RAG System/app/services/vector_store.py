"""
ChromaDB vector store wrapper with tenant isolation.
Each tenant gets its own ChromaDB collection.
Includes TTL-based caching for search results.
"""

import hashlib
import logging
import threading
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)

# ── Search result cache (TTL 5 minutes, max 256 entries) ────────────────
_cache: dict[str, tuple[float, list[dict]]] = {}
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
            ts, value = _cache[key]
            if time.time() - ts < _CACHE_TTL_SECONDS:
                logger.debug("Cache hit for search key %s", key[:12])
                return value
            del _cache[key]
    return None


def _cache_set(key: str, value: list[dict]) -> None:
    """Store value in cache with current timestamp."""
    import time

    with _cache_lock:
        # Evict oldest if at capacity
        if len(_cache) >= _CACHE_MAX_SIZE and key not in _cache:
            oldest_key = min(_cache, key=lambda k: _cache[k][0])
            del _cache[oldest_key]
        _cache[key] = (time.time(), value)


def invalidate_cache(tenant_id: UUID, document_id: UUID | None = None) -> None:
    """Invalidate cached search results for a tenant (or specific document)."""
    prefix = str(tenant_id)
    with _cache_lock:
        _cache.clear()
    logger.debug("Search cache cleared for tenant %s", prefix)


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
        return cached

    client = _get_client()

    try:
        collection = client.get_collection(name=_collection_name(tenant_id))
    except Exception:
        return []

    where_filter = None
    if document_id:
        where_filter = {"document_id": str(document_id)}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter,
    )

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

    # Store in cache
    _cache_set(key, items)

    return items


def delete_document_chunks(tenant_id: UUID, document_id: UUID) -> None:
    """Delete all chunks for a document from ChromaDB."""
    client = _get_client()
    try:
        collection = client.get_collection(name=_collection_name(tenant_id))
        collection.delete(where={"document_id": str(document_id)})
        invalidate_cache(tenant_id, document_id)
    except Exception:
        pass
