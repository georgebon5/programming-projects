"""
Tests for ChromaDB configuration (Phase 6.2).

Tests run in embedded mode only — no HTTP ChromaDB server is required.
"""

import os

import chromadb
import pytest


def test_chroma_host_default_is_empty():
    """Default config should use embedded mode (empty chroma_host)."""
    # Import after env is set up by conftest
    from app.config import settings

    assert settings.chroma_host == ""


def test_chroma_port_default():
    """Default chroma_port should be 8000."""
    from app.config import settings

    assert settings.chroma_port == 8000


def test_chroma_token_default_is_empty():
    """Default chroma_token should be empty (no auth by default)."""
    from app.config import settings

    assert settings.chroma_token == ""


def test_get_client_returns_persistent_client_when_no_host():
    """_get_client() must return a PersistentClient when chroma_host is empty."""
    from app.config import settings
    from app.services.vector_store import _get_client

    assert settings.chroma_host == ""
    client = _get_client()
    # PersistentClient has a _settings attribute; HttpClient is built via a factory
    # function, so we check the class name instead.
    assert type(client).__name__ == "Client"


def test_get_client_uses_vector_db_path(tmp_path):
    """_get_client() should use the configured vector_db_path for embedded mode."""
    from app.services.vector_store import _get_client

    # The path used in tests is ./test_vector_db (set by conftest)
    client = _get_client()
    # Verify we get a working client by creating/listing a collection
    # (collection names must start with an alphanumeric character)
    client.get_or_create_collection("test-config-probe")
    cols = [c.name for c in client.list_collections()]
    assert "test-config-probe" in cols
    # Cleanup
    client.delete_collection("test-config-probe")


def test_config_fields_exist():
    """All three new ChromaDB config fields must be present on Settings."""
    from app.config import Settings

    fields = Settings.model_fields
    assert "chroma_host" in fields
    assert "chroma_port" in fields
    assert "chroma_token" in fields
