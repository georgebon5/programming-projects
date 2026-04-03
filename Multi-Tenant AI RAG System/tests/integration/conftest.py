"""
Integration test fixtures using a real PostgreSQL container.
Tests are automatically skipped if Docker is not available.
"""
import os
import uuid

import pytest

# Skip all integration tests if Docker is not available
try:
    from testcontainers.postgres import PostgresContainer
    import docker
    docker.from_env().ping()
    HAS_DOCKER = True
except Exception:
    HAS_DOCKER = False

pytestmark = pytest.mark.skipif(not HAS_DOCKER, reason="Docker not available — skipping integration tests")


@pytest.fixture(scope="module")
def postgres_container():
    """Start a PostgreSQL container for the test module."""
    if not HAS_DOCKER:
        pytest.skip("Docker not available")

    with PostgresContainer("postgres:15-alpine") as pg:
        yield pg


@pytest.fixture(scope="function")
def pg_engine(postgres_container):
    """Create a SQLAlchemy engine connected to the test PostgreSQL."""
    from sqlalchemy import create_engine
    from app.db.database import Base

    url = postgres_container.get_connection_url()
    engine = create_engine(url, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def pg_session(pg_engine):
    """Create a SQLAlchemy session for the test."""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=pg_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def create_test_tenant(session, slug=None):
    """Helper to create a tenant with admin user in PostgreSQL."""
    from app.models.tenant import Tenant
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    slug = slug or f"test-{uuid.uuid4().hex[:8]}"

    tenant = Tenant(
        name=f"Test Tenant {slug}",
        slug=slug,
        is_active=True,
        subscription_tier="free",
    )
    session.add(tenant)
    session.flush()

    user = User(
        tenant_id=tenant.id,
        username="admin",
        email=f"admin@{slug}.com",
        hashed_password=hash_password("Password1234!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(tenant)
    session.refresh(user)

    return tenant, user
