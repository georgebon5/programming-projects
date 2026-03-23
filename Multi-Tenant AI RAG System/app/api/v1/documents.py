from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.document_service import DocumentService
from app.utils.exceptions import DocumentNotFound

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(require_role({UserRole.ADMIN, UserRole.MEMBER})),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    file_content = await file.read()

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

    return DocumentResponse.model_validate(doc)


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    service = DocumentService(db)
    docs, total = service.list_documents(current_user.tenant_id, skip=skip, limit=limit)
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
        service.delete_document(document_id, current_user.tenant_id)
    except DocumentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
