"""
Locust load testing for Multi-Tenant RAG API.

Run:
    pip install locust
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Open http://localhost:8089 in your browser to configure and start the test.
"""

import json
import random
import string

from locust import HttpUser, between, task


def _random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


class RAGUser(HttpUser):
    """Simulates a typical user interacting with the RAG API."""

    wait_time = between(1, 3)

    # Shared state
    token: str = ""
    tenant_slug: str = ""
    documents: list[str] = []
    conversation_id: str = ""

    def on_start(self) -> None:
        """Register a fresh tenant and log in."""
        slug = f"load-{_random_string(6)}"
        self.tenant_slug = slug

        # Register
        resp = self.client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": f"Load Test {slug}",
                "tenant_slug": slug,
                "username": "loadtest",
                "email": f"{slug}@loadtest.local",
                "password": "LoadTest123!",
            },
        )
        if resp.status_code != 201:
            return

        # Login
        resp = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"{slug}@loadtest.local",
                "password": "LoadTest123!",
            },
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def health_check(self) -> None:
        self.client.get("/health")

    @task(2)
    def get_current_user(self) -> None:
        self.client.get("/api/v1/auth/me", headers=self._headers)

    @task(5)
    def list_documents(self) -> None:
        self.client.get("/api/v1/documents/", headers=self._headers)

    @task(2)
    def upload_document(self) -> None:
        content = f"Load test document content {_random_string(200)}"
        files = {"file": (f"test_{_random_string()}.txt", content.encode(), "text/plain")}
        resp = self.client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=self._headers,
        )
        if resp.status_code == 201:
            doc_id = resp.json().get("id")
            if doc_id:
                self.documents.append(doc_id)

    @task(10)
    def chat_question(self) -> None:
        questions = [
            "What is mentioned in the documents?",
            "Can you summarize the key points?",
            "What are the main topics?",
            "Tell me about the content.",
            "What data is available?",
        ]
        payload: dict = {"question": random.choice(questions)}
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id

        resp = self.client.post(
            "/api/v1/chat/",
            json=payload,
            headers=self._headers,
        )
        if resp.status_code == 200:
            self.conversation_id = resp.json().get("conversation_id", "")

    @task(3)
    def list_conversations(self) -> None:
        self.client.get("/api/v1/chat/", headers=self._headers)

    @task(1)
    def list_users(self) -> None:
        self.client.get("/api/v1/users/", headers=self._headers)

    @task(1)
    def get_tenant_settings(self) -> None:
        self.client.get("/api/v1/tenant/settings", headers=self._headers)

    @task(1)
    def get_metrics(self) -> None:
        self.client.get("/metrics")
