from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    uploaded_by_id: Optional[UUID] = None
    filename: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    status: DocumentStatus
    error_message: Optional[str] = None
    content_preview: Optional[str] = None
    total_chunks: int
    created_at: datetime
    processed_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
