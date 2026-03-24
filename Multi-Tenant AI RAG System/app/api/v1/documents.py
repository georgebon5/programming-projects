import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db, get_session_factory
from app.dependencies.auth import get_current_user, require_role
from app.models.audit_log import AuditAction
from app.models.user import User, UserRole
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService
from app.services.tenant_settings_service import QuotaExceeded, TenantSettingsService
from app.services.vector_store import delete_document_chunks
from app.utils.exceptions import DocumentNotFound, DocumentProcessingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


def _process_document_background(document_id: UUID, tenant_id: UUID) -> None:
    """Background task: process a document in its own DB session."""
    db = get_session_factory()()
    try:
        processing = ProcessingService(db)
        processing.process_document(document_id, tenant_id)
    except Exception as exc:
        logger.error("Background processing failed for document %s: %s", document_id, exc)
    finally:
        db.close()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role({UserRole.ADMIN, UserRole.MEMBER})),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    file_content = await file.read()

    # Check quotas
    quota_svc = TenantSettingsService(db)
    try:
        quota_svc.check_upload_enabled(current_user.tenant_id)
        quota_svc.check_document_quota(current_user.tenant_id)
        quota_svc.check_storage_quota(current_user.tenant_id, len(file_content))
    except QuotaExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    service = DocumentService(db)
    try:
        doc = service.upload_document(
            tenant_id=current_user.tenant_id,
            uploaded_by_id=current_user.id,
            file=file,
            file_content=file_content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Schedule processing as background task (non-blocking)
    background_tasks.add_task(_process_document_background, doc.id, current_user.tenant_id)

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.DOCUMENT_UPLOAD,
        resource_type="document",
        resource_id=str(doc.id),
        details={"filename": doc.original_filename, "size_bytes": doc.file_size_bytes},
    )

    return DocumentResponse.model_validate(doc)


@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document(
    document_id: UUID,
    current_user: User = Depends(require_role({UserRole.ADMIN, UserRole.MEMBER})),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Manually trigger (re)processing of a document."""
    processing = ProcessingService(db)
    try:
        doc = processing.process_document(document_id, current_user.tenant_id)
    except DocumentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DocumentResponse.model_validate(doc)


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None, description="Filter by status: uploaded, processing, completed, failed"),
    search: str | None = Query(None, max_length=200, description="Search by filename"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    service = DocumentService(db)
    docs, total = service.list_documents(
        current_user.tenant_id,
        skip=skip,
        limit=limit,
        status_filter=status,
        search=search,
    )
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    service = DocumentService(db)
    try:
        doc = service.get_document(document_id, current_user.tenant_id)
    except DocumentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    current_user: User = Depends(require_role({UserRole.ADMIN, UserRole.MEMBER})),
    db: Session = Depends(get_db),
) -> None:
    service = DocumentService(db)
    try:
        # Delete from ChromaDB first
        delete_document_chunks(current_user.tenant_id, document_id)
        service.delete_document(document_id, current_user.tenant_id)
    except DocumentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.DOCUMENT_DELETE,
        resource_type="document",
        resource_id=str(document_id),
    )
