"""Test concurrent access patterns with real PostgreSQL."""
import pytest
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import sessionmaker
from tests.integration.conftest import create_test_tenant

pytestmark = pytest.mark.skipif(
    not __import__('tests.integration.conftest', fromlist=['HAS_DOCKER']).HAS_DOCKER,
    reason="Docker not available"
)


class TestConcurrentAccessPG:
    def test_concurrent_user_creation(self, pg_engine):
        """Multiple users can be created concurrently in the same tenant."""
        from app.models.tenant import Tenant
        from app.models.user import User, UserRole
        from app.utils.security import hash_password

        Session = sessionmaker(bind=pg_engine)

        # Create tenant first
        session = Session()
        tenant = Tenant(name="Concurrent", slug=f"conc-{uuid.uuid4().hex[:6]}", is_active=True, subscription_tier="free")
        session.add(tenant)
        session.commit()
        tenant_id = tenant.id
        session.close()

        def create_user(i):
            s = Session()
            try:
                u = User(
                    tenant_id=tenant_id,
                    username=f"user_{i}",
                    email=f"user_{i}@concurrent.com",
                    hashed_password=hash_password("Password1234!"),
                    role=UserRole.MEMBER,
                    is_active=True,
                )
                s.add(u)
                s.commit()
                return True
            except Exception:
                s.rollback()
                return False
            finally:
                s.close()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_user, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        assert all(results), "Some concurrent user creations failed"

        # Verify all users were created
        session = Session()
        count = session.query(User).filter(User.tenant_id == tenant_id).count()
        session.close()
        assert count == 10

    def test_concurrent_document_creation(self, pg_engine):
        """Multiple documents can be uploaded concurrently."""
        from app.models.document import Document, DocumentStatus

        Session = sessionmaker(bind=pg_engine)

        session = Session()
        from tests.integration.conftest import create_test_tenant
        tenant, user = create_test_tenant(session)
        tenant_id = tenant.id
        user_id = user.id
        session.close()

        def create_doc(i):
            s = Session()
            try:
                d = Document(
                    tenant_id=tenant_id,
                    uploaded_by_id=user_id,
                    filename=f"doc_{i}.pdf",
                    original_filename=f"doc_{i}.pdf",
                    file_path=f"/tmp/doc_{i}.pdf",
                    mime_type="application/pdf",
                    file_size_bytes=1024 * (i + 1),
                    status=DocumentStatus.UPLOADED,
                )
                s.add(d)
                s.commit()
                return True
            except Exception:
                s.rollback()
                return False
            finally:
                s.close()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_doc, i) for i in range(20)]
            results = [f.result() for f in as_completed(futures)]

        assert all(results)

        session = Session()
        count = session.query(Document).filter(Document.tenant_id == tenant_id).count()
        session.close()
        assert count == 20
