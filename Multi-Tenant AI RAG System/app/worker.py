"""
Celery worker configuration & tasks.

Start the worker:
    celery -A app.worker worker --loglevel=info

In development the app falls back to FastAPI BackgroundTasks automatically
when Celery/Redis is not available.
"""

import logging
from uuid import UUID

from celery import Celery
from celery.schedules import crontab

from app.config import settings

logger = logging.getLogger(__name__)

broker_url = settings.celery_broker_url or settings.redis_url
result_backend = settings.celery_result_backend or settings.redis_url

celery_app = Celery(
    "rag_worker",
    broker=broker_url,
    backend=result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_document_task(self, document_id: str, tenant_id: str) -> dict:
    """Process a document asynchronously via Celery."""
    from app.db.database import get_session_factory
    from app.services.processing_service import ProcessingService

    db = get_session_factory()()
    try:
        processing = ProcessingService(db)
        doc = processing.process_document(UUID(document_id), UUID(tenant_id))
        return {"status": doc.status.value, "document_id": document_id}
    except Exception as exc:
        logger.error("Celery task failed for document %s: %s", document_id, exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def cleanup_expired_tokens_task(self) -> dict:
    """Periodic cleanup of expired tokens."""
    from app.db.database import get_session_factory
    from app.services.cleanup_service import CleanupService

    db = get_session_factory()()
    try:
        service = CleanupService(db)
        return service.cleanup_expired_tokens()
    except Exception as exc:
        logger.error("Cleanup task failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "app.worker.cleanup_expired_tokens_task",
        "schedule": crontab(hour=3, minute=0),
    },
}
celery_app.conf.timezone = "UTC"


def is_celery_available() -> bool:
    """Check if the Celery broker (Redis) is reachable."""
    try:
        celery_app.connection_for_write().ensure_connection(max_retries=0)
        return True
    except Exception:
        return False
