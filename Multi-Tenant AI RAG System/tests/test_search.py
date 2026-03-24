"""
Tests for enhanced features: document search/filtering, health check.
"""

import io

from tests.conftest import auth_header, register_tenant


class TestDocumentSearch:
    def test_search_by_filename(self, client):
        """Search documents by filename."""
        _, token = register_tenant(client, "search")
        content = "Search test. " * 50
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("report.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("notes.txt", io.BytesIO(content.encode()), "text/plain")},
        )

        # Search for "report"
        resp = client.get(
            "/api/v1/documents/?search=report",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "report" in data["documents"][0]["original_filename"]

    def test_filter_by_status(self, client):
        """Filter documents by processing status."""
        _, token = register_tenant(client, "search-status")
        content = "Filter test. " * 50
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
        )

        resp = client.get(
            "/api/v1/documents/?status=completed",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = client.get(
            "/api/v1/documents/?status=uploaded",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_combined_search_and_filter(self, client):
        """Search + status filter combined."""
        _, token = register_tenant(client, "search-comb")
        content = "Combined test content. " * 50
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("alpha.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("beta.txt", io.BytesIO(content.encode()), "text/plain")},
        )

        resp = client.get(
            "/api/v1/documents/?search=alpha&status=completed",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestEnhancedHealth:
    def test_health_fields(self, client):
        """Health check returns enhanced fields."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert "python_version" in data
        assert data["version"] == "0.3.0"
