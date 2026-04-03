"""Test cascade delete behavior with real PostgreSQL foreign keys."""
import pytest
import uuid

from tests.integration.conftest import create_test_tenant

pytestmark = pytest.mark.skipif(
    not __import__('tests.integration.conftest', fromlist=['HAS_DOCKER']).HAS_DOCKER,
    reason="Docker not available"
)


class TestCascadeDeletesPG:
    def test_deleting_tenant_cascades_to_users(self, pg_session):
        """Deleting a tenant removes all its users."""
        from app.models.tenant import Tenant
        from app.models.user import User

        tenant, user = create_test_tenant(pg_session)
        tenant_id = tenant.id

        pg_session.delete(tenant)
        pg_session.commit()

        assert pg_session.query(Tenant).filter(Tenant.id == tenant_id).first() is None
        assert pg_session.query(User).filter(User.tenant_id == tenant_id).all() == []

    def test_deleting_tenant_cascades_to_documents(self, pg_session):
        """Deleting a tenant removes all its documents."""
        from app.models.document import Document, DocumentStatus
        from app.models.tenant import Tenant

        tenant, user = create_test_tenant(pg_session)

        doc = Document(
            tenant_id=tenant.id,
            uploaded_by_id=user.id,
            filename="cascade_test.pdf",
            original_filename="cascade_test.pdf",
            file_path="/tmp/cascade_test.pdf",
            mime_type="application/pdf",
            file_size_bytes=100,
            status=DocumentStatus.UPLOADED,
        )
        pg_session.add(doc)
        pg_session.commit()
        doc_id = doc.id

        pg_session.delete(tenant)
        pg_session.commit()

        assert pg_session.query(Document).filter(Document.id == doc_id).first() is None

    def test_deleting_tenant_cascades_to_chat_messages(self, pg_session):
        """Deleting a tenant removes all chat messages."""
        from app.models.chat import ChatMessage, MessageRole
        from app.models.tenant import Tenant

        tenant, user = create_test_tenant(pg_session)

        msg = ChatMessage(
            tenant_id=tenant.id,
            user_id=user.id,
            conversation_id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content="Test message",
        )
        pg_session.add(msg)
        pg_session.commit()

        pg_session.delete(tenant)
        pg_session.commit()

        remaining = pg_session.query(ChatMessage).filter(ChatMessage.tenant_id == tenant.id).all()
        assert remaining == []

    def test_deleting_user_does_not_delete_tenant(self, pg_session):
        """Deleting a user should not cascade up to the tenant."""
        from app.models.tenant import Tenant
        from app.models.user import User

        tenant, user = create_test_tenant(pg_session)
        tenant_id = tenant.id

        pg_session.delete(user)
        pg_session.commit()

        assert pg_session.query(Tenant).filter(Tenant.id == tenant_id).first() is not None
