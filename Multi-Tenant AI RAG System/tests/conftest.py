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

import app.db.database as _db_mod
from app.db.database import Base, get_db
from app.main import app

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

# Override session factory so background tasks also use the test DB
_original_get_session_factory = _db_mod.get_session_factory


def _test_get_session_factory():
    return TestSession


_db_mod.get_session_factory = _test_get_session_factory


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
        "password": "Password1234!",
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


@pytest.fixture()
def admin_token(client):
    """Register a tenant and return the admin token."""
    _, token = register_tenant(client, f"admin-{uuid.uuid4().hex[:6]}")
    return token


@pytest.fixture()
def admin_token_alt(client):
    """Register a second tenant and return its admin token."""
    _, token = register_tenant(client, f"alt-{uuid.uuid4().hex[:6]}")
    return token


@pytest.fixture()
def member_token(client):
    """Register a tenant, create a member user, and return member token."""
    _, admin_tok = register_tenant(client, f"mem-{uuid.uuid4().hex[:6]}")
    # Create a member user via admin
    member_email = f"member-{uuid.uuid4().hex[:6]}@test.com"
    resp = client.post(
        "/api/v1/users/invite",
        json={
            "username": "member",
            "email": member_email,
            "password": "Password1234!",
            "role": "member",
        },
        headers=auth_header(admin_tok),
    )
    assert resp.status_code == 201, resp.text
    # Login as member
    login = client.post(
        "/api/v1/auth/login",
        json={"email": member_email, "password": "Password1234!"},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]
