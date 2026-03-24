import os
import uuid as uuid_mod
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentStatus
from app.utils.exceptions import DocumentNotFound

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upload_document(
        self,
        *,
        tenant_id: UUID,
        uploaded_by_id: UUID,
        file: UploadFile,
        file_content: bytes,
    ) -> Document:
        original_filename = file.filename or "unknown"
        ext = Path(original_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

        file_size = len(file_content)
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(f"File exceeds maximum size of {settings.max_file_size_mb}MB")

        # Build safe storage path: uploads/<tenant_id>/<uuid><ext>
        safe_filename = f"{uuid_mod.uuid4()}{ext}"
        tenant_dir = Path(settings.upload_dir) / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)
        file_path = tenant_dir / safe_filename

        file_path.write_bytes(file_content)

        mime_type = file.content_type or "application/octet-stream"

        doc = Document(
            tenant_id=tenant_id,
            uploaded_by_id=uploaded_by_id,
            filename=safe_filename,
            original_filename=original_filename,
            file_path=str(file_path),
            file_size_bytes=file_size,
            mime_type=mime_type,
            status=DocumentStatus.UPLOADED,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_documents(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Document], int]:
        query = self.db.query(Document).filter(Document.tenant_id == tenant_id)

        if status_filter:
            try:
                status_enum = DocumentStatus(status_filter)
                query = query.filter(Document.status == status_enum)
            except ValueError:
                pass  # Ignore invalid status filter

        if search:
            query = query.filter(Document.original_filename.ilike(f"%{search}%"))

        total = query.count()
        docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
        return docs, total

    def get_document(self, document_id: UUID, tenant_id: UUID) -> Document:
        doc = (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.tenant_id == tenant_id)
            .first()
        )
        if not doc:
            raise DocumentNotFound("Document not found")
        return doc

    def delete_document(self, document_id: UUID, tenant_id: UUID) -> None:
        doc = self.get_document(document_id, tenant_id)

        # Delete file from disk
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        self.db.delete(doc)
        self.db.commit()
