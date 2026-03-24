from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    uploaded_by_id: UUID | None = None
    filename: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    status: DocumentStatus
    error_message: str | None = None
    content_preview: str | None = None
    total_chunks: int
    created_at: datetime
    processed_at: datetime | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentSearchResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    query: str | None = None
    status_filter: str | None = None
