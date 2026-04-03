"""Test tenant data isolation with real PostgreSQL constraints."""
import pytest
import uuid

from tests.integration.conftest import create_test_tenant

pytestmark = pytest.mark.skipif(
    not __import__('tests.integration.conftest', fromlist=['HAS_DOCKER']).HAS_DOCKER,
    reason="Docker not available"
)


class TestTenantIsolationPG:
    def test_users_isolated_between_tenants(self, pg_session):
        """Users from tenant A are not visible when querying tenant B."""
        from app.models.user import User

        tenant_a, user_a = create_test_tenant(pg_session, "iso-a")
        tenant_b, user_b = create_test_tenant(pg_session, "iso-b")

        users_a = pg_session.query(User).filter(User.tenant_id == tenant_a.id).all()
        users_b = pg_session.query(User).filter(User.tenant_id == tenant_b.id).all()

        assert len(users_a) == 1
        assert len(users_b) == 1
        assert users_a[0].id != users_b[0].id
        assert users_a[0].tenant_id == tenant_a.id
        assert users_b[0].tenant_id == tenant_b.id

    def test_documents_isolated_between_tenants(self, pg_session):
        """Documents are scoped to their tenant."""
        from app.models.document import Document, DocumentStatus

        tenant_a, user_a = create_test_tenant(pg_session, "doc-iso-a")
        tenant_b, user_b = create_test_tenant(pg_session, "doc-iso-b")

        doc_a = Document(
            tenant_id=tenant_a.id,
            uploaded_by_id=user_a.id,
            filename="test_a.pdf",
            original_filename="test_a.pdf",
            file_path="/tmp/test_a.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
            status=DocumentStatus.UPLOADED,
        )
        doc_b = Document(
            tenant_id=tenant_b.id,
            uploaded_by_id=user_b.id,
            filename="test_b.pdf",
            original_filename="test_b.pdf",
            file_path="/tmp/test_b.pdf",
            mime_type="application/pdf",
            file_size_bytes=2048,
            status=DocumentStatus.UPLOADED,
        )
        pg_session.add_all([doc_a, doc_b])
        pg_session.commit()

        docs_a = pg_session.query(Document).filter(Document.tenant_id == tenant_a.id).all()
        docs_b = pg_session.query(Document).filter(Document.tenant_id == tenant_b.id).all()

        assert len(docs_a) == 1
        assert len(docs_b) == 1
        assert docs_a[0].original_filename == "test_a.pdf"
        assert docs_b[0].original_filename == "test_b.pdf"

    def test_same_email_allowed_in_different_tenants(self, pg_session):
        """Same email can exist in two different tenants."""
        from app.models.user import User, UserRole
        from app.utils.security import hash_password
        from app.models.tenant import Tenant

        tenant_a = Tenant(name="A", slug=f"dup-a-{uuid.uuid4().hex[:6]}", is_active=True, subscription_tier="free")
        tenant_b = Tenant(name="B", slug=f"dup-b-{uuid.uuid4().hex[:6]}", is_active=True, subscription_tier="free")
        pg_session.add_all([tenant_a, tenant_b])
        pg_session.flush()

        user_a = User(tenant_id=tenant_a.id, username="admin", email="shared@example.com",
                      hashed_password=hash_password("Password1234!"), role=UserRole.ADMIN, is_active=True)
        user_b = User(tenant_id=tenant_b.id, username="admin", email="shared@example.com",
                      hashed_password=hash_password("Password1234!"), role=UserRole.ADMIN, is_active=True)
        pg_session.add_all([user_a, user_b])
        pg_session.commit()

        all_shared = pg_session.query(User).filter(User.email == "shared@example.com").all()
        assert len(all_shared) == 2
