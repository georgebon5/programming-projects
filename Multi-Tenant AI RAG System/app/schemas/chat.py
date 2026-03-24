from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import MessageRole


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=255)
    document_id: UUID | None = None
    n_context_chunks: int = Field(default=5, ge=1, le=20)


class SourceChunk(BaseModel):
    text: str
    document_id: str | None = None
    chunk_index: int | None = None
    distance: float | None = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: list[SourceChunk]


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: list[ChatMessageResponse]


class ConversationSummary(BaseModel):
    conversation_id: str
    message_count: int
    started_at: str | None = None
    last_message_at: str | None = None
    preview: str = ""


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]
    total: int
