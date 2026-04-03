import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.db.database import get_db, get_session_factory
from app.dependencies.auth import get_current_user, require_role
from app.models.audit_log import AuditAction
from app.models.document import Document as DocumentModel, DocumentStatus
from app.models.user import User, UserRole
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.audit_service import AuditService
from app.services.cache_service import CacheService
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService
from app.services.storage import get_storage_backend
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


# ── Static-path routes (must come before /{document_id} routes) ──────────────

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

    # Schedule processing — prefer Celery if available, fallback to BackgroundTasks
    try:
        from app.worker import is_celery_available, process_document_task

        if is_celery_available():
            process_document_task.delay(str(doc.id), str(current_user.tenant_id))
        else:
            background_tasks.add_task(_process_document_background, doc.id, current_user.tenant_id)
    except Exception:
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

    CacheService().invalidate("usage", str(current_user.tenant_id))

    return DocumentResponse.model_validate(doc)


@router.post("/bulk", response_model=list[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def bulk_upload(
    files: list[UploadFile],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role({UserRole.ADMIN, UserRole.MEMBER})),
    db: Session = Depends(get_db),
) -> list[DocumentResponse]:
    """Upload multiple documents in one request (max 10 files)."""
    if len(files) > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 10 files per batch")

    # Read all file contents up front so we can validate before persisting any
    file_contents: list[tuple[UploadFile, bytes]] = []
    for f in files:
        content = await f.read()
        file_contents.append((f, content))

    # Validate all files before touching the DB
    quota_svc = TenantSettingsService(db)
    try:
        quota_svc.check_upload_enabled(current_user.tenant_id)
    except QuotaExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    from app.services.document_service import ALLOWED_EXTENSIONS
    from pathlib import Path as _Path
    for f, content in file_contents:
        ext = _Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{f.filename}': type '{ext}' not allowed.",
            )
        max_bytes = 20 * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{f.filename}' exceeds maximum size.",
            )

    # Persist all documents
    service = DocumentService(db)
    created_docs: list[DocumentResponse] = []
    for f, content in file_contents:
        try:
            quota_svc.check_document_quota(current_user.tenant_id)
            quota_svc.check_storage_quota(current_user.tenant_id, len(content))
        except QuotaExceeded as exc:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

        doc = service.upload_document(
            tenant_id=current_user.tenant_id,
            uploaded_by_id=current_user.id,
            file=f,
            file_content=content,
        )

        # Queue processing
        try:
            from app.worker import is_celery_available, process_document_task
            if is_celery_available():
                process_document_task.delay(str(doc.id), str(current_user.tenant_id))
            else:
                background_tasks.add_task(_process_document_background, doc.id, current_user.tenant_id)
        except Exception:
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
        created_docs.append(DocumentResponse.model_validate(doc))

    return created_docs


@router.post("/reprocess-all", response_model=dict)
def reprocess_all_documents(
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> dict:
    """Queue all completed documents for reprocessing (admin only)."""
    docs = (
        db.query(DocumentModel)
        .filter(
            DocumentModel.tenant_id == current_user.tenant_id,
            DocumentModel.status == DocumentStatus.COMPLETED,
            DocumentModel.deleted_at.is_(None),
        )
        .all()
    )
    queued = 0
    try:
        from app.worker import is_celery_available, process_document_task
        use_celery = is_celery_available()
    except Exception:
        use_celery = False

    for doc in docs:
        # Reset to UPLOADED so process_document accepts it
        doc.status = DocumentStatus.UPLOADED
        doc.total_chunks = 0
        doc.error_message = None

    db.commit()

    for doc in docs:
        if use_celery:
            process_document_task.delay(str(doc.id), str(current_user.tenant_id))
        queued += 1

    return {"queued": queued}


@router.get("/deleted", response_model=DocumentListResponse)
def list_deleted_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    """List soft-deleted documents (admin only)."""
    service = DocumentService(db)
    docs, total = service.list_deleted_documents(current_user.tenant_id, skip=skip, limit=limit)
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
    )


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


# ── Parameterised routes ──────────────────────────────────────────────────────

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


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    document_id: UUID,
    current_user: User = Depends(require_role({UserRole.ADMIN, UserRole.MEMBER})),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Re-process a single completed or failed document."""
    processing = ProcessingService(db)
    try:
        doc = processing.reprocess_document(document_id, current_user.tenant_id)
    except DocumentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DocumentResponse.model_validate(doc)


@router.post("/{document_id}/restore", response_model=DocumentResponse)
def restore_document(
    document_id: UUID,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Restore a soft-deleted document (admin only)."""
    service = DocumentService(db)
    try:
        doc = service.restore_document(document_id, current_user.tenant_id)
    except DocumentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DocumentResponse.model_validate(doc)


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


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download the original uploaded file."""
    service = DocumentService(db)
    try:
        doc = service.get_document(document_id, current_user.tenant_id)
    except DocumentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    file_path = Path(doc.file_path)
    storage = get_storage_backend()

    if not storage.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage",
        )

    # For local storage we can use FileResponse; for S3 we stream the bytes
    if file_path.is_file():
        return FileResponse(
            path=file_path,
            filename=doc.original_filename,
            media_type=doc.mime_type or "application/octet-stream",
        )

    content = storage.read(doc.file_path)
    return Response(
        content=content,
        media_type=doc.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.original_filename}"'},
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    current_user: User = Depends(require_role({UserRole.ADMIN, UserRole.MEMBER})),
    db: Session = Depends(get_db),
) -> None:
    service = DocumentService(db)
    try:
        service.delete_document(document_id, current_user.tenant_id, deleted_by_id=current_user.id)
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

    CacheService().invalidate("usage", str(current_user.tenant_id))
