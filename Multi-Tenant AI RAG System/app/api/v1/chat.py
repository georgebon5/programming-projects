from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    SourceChunk,
)
from app.services.chat_service import ChatService
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Ask a question over your tenant's documents using RAG."""
    service = ChatService(db)
    result = service.chat(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        question=payload.question,
        conversation_id=payload.conversation_id,
        document_id=payload.document_id,
        n_context_chunks=payload.n_context_chunks,
    )

    return ChatResponse(
        answer=result["answer"],
        conversation_id=result["conversation_id"],
        sources=[SourceChunk(**s) for s in result["sources"]],
    )


@router.get("/{conversation_id}", response_model=ConversationHistoryResponse)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationHistoryResponse:
    """Get the full message history of a conversation."""
    service = ChatService(db)
    messages = service.get_conversation(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
    )
