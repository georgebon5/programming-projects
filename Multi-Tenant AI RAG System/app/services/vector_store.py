"""
ChromaDB vector store wrapper with tenant isolation.
Each tenant gets its own ChromaDB collection.
"""

from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


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

    return ids


def search_chunks(
    tenant_id: UUID,
    query: str,
    n_results: int = 5,
    document_id: UUID | None = None,
) -> list[dict]:
    """
    Search for relevant chunks in a tenant's collection.

    Returns list of dicts with keys: text, document_id, chunk_index, distance.
    """
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

    return items


def delete_document_chunks(tenant_id: UUID, document_id: UUID) -> None:
    """Delete all chunks for a document from ChromaDB."""
    client = _get_client()
    try:
        collection = client.get_collection(name=_collection_name(tenant_id))
        collection.delete(where={"document_id": str(document_id)})
    except Exception:
        pass
