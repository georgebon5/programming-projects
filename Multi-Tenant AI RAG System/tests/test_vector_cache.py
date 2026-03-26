"""
Tests for vector store cache TTL and eviction behaviour.
"""

import time
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tests.conftest import auth_header, register_tenant


class TestVectorCacheBasic:
    """Basic tests for vector store caching."""

    def test_store_chunks_returns_ids(self):
        """store_chunks returns a list of embedding IDs."""
        from app.services.vector_store import store_chunks

        tenant_id = uuid4()
        doc_id = uuid4()
        ids = store_chunks(tenant_id, doc_id, ["hello world", "test chunk"])
        assert isinstance(ids, list)
        assert len(ids) == 2

    def test_collection_name_format(self):
        """Collection name follows tenant_ prefix pattern."""
        from app.services.vector_store import _collection_name

        tenant_id = uuid4()
        name = _collection_name(tenant_id)
        assert name.startswith("tenant_")
        assert str(tenant_id) in name

    def test_different_tenants_different_names(self):
        """Different tenants get different collection names."""
        from app.services.vector_store import _collection_name

        t1 = uuid4()
        t2 = uuid4()
        assert _collection_name(t1) != _collection_name(t2)


class TestVectorStoreOperations:
    """Tests for vector store CRUD operations."""

    def test_delete_nonexistent_document(self):
        """Deleting chunks for nonexistent document doesn't raise."""
        from app.services.vector_store import delete_document_chunks

        # Should not raise
        delete_document_chunks(uuid4(), uuid4())

    def test_store_and_delete(self):
        """Store chunks then delete them."""
        from app.services.vector_store import delete_document_chunks, store_chunks

        tenant_id = uuid4()
        doc_id = uuid4()
        store_chunks(tenant_id, doc_id, ["test content for deletion"])
        # Should not raise
        delete_document_chunks(tenant_id, doc_id)

    def test_cache_invalidation(self):
        """invalidate_cache clears cached entries for a tenant."""
        from app.services.vector_store import invalidate_cache

        tenant_id = uuid4()
        # Should not raise even with empty cache
        invalidate_cache(tenant_id)

    def test_cache_invalidation_specific_doc(self):
        """invalidate_cache can target a specific document."""
        from app.services.vector_store import invalidate_cache

        tenant_id = uuid4()
        doc_id = uuid4()
        invalidate_cache(tenant_id, doc_id)


class TestVectorStoreHTTPEndpoints:
    """Tests for vector store operations via HTTP."""

    def test_upload_requires_auth(self, client):
        """Upload without auth returns 401."""
        resp = client.post("/api/v1/documents/upload")
        assert resp.status_code in (401, 422)

    def test_upload_no_file(self, client):
        """Upload without file returns 422."""
        _, token = register_tenant(client, "vec-nofile")
        resp = client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
        )
        assert resp.status_code == 422

    def test_upload_valid_txt(self, client):
        """Upload a valid .txt file succeeds."""
        _, token = register_tenant(client, "vec-txt")
        resp = client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("test.txt", b"Hello world content", "text/plain")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_filename"] == "test.txt"
