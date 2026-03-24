"""
Shared test fixtures: in-memory SQLite DB, TestClient, auth helpers.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Override settings BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_unit.db"
os.environ["DEBUG"] = "true"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["VECTOR_DB_PATH"] = "./test_vector_db"

from app.db.database import Base, get_db
from app.main import app
from app.utils.security import create_access_token

# In-memory SQLite for tests
TEST_ENGINE = create_engine(
    "sqlite:///./test_unit.db",
    connect_args={"check_same_thread": False},
    echo=False,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    original_limiter_enabled = app.state.limiter.enabled
    app.state.limiter.enabled = False
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)
    app.state.limiter.enabled = original_limiter_enabled


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


# ── Helper: register tenant + get token ──────────────────────────────────

def register_tenant(client: TestClient, slug: str | None = None):
    """Register a tenant + admin and return (user_data, token)."""
    slug = slug or f"test-{uuid.uuid4().hex[:8]}"
    payload = {
        "tenant_name": f"Test Tenant {slug}",
        "tenant_slug": slug,
        "username": "admin",
        "email": f"admin@{slug}.com",
        "password": "password1234",
    }
    resp = client.post("/api/v1/auth/register-tenant-admin", json=payload)
    assert resp.status_code == 201, resp.text
    user = resp.json()

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    return user, token


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
