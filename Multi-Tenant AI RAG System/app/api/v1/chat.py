import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.db.database import get_db, get_session_factory
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationSummary,
    SourceChunk,
)
from app.services.audit_service import AuditService
from app.services.chat_service import ChatService
from app.services.tenant_settings_service import QuotaExceeded, TenantSettingsService
from app.utils.rate_limit import limiter
from app.utils.sanitize import sanitize_chat_message
from app.utils.security import decode_access_token, TokenPayloadError
from app.config import settings as app_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
@limiter.limit(lambda: app_settings.rate_limit_chat)
def chat(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Ask a question over your tenant's documents using RAG."""
    # Check chat quota
    quota_svc = TenantSettingsService(db)
    try:
        quota_svc.check_chat_quota(current_user.tenant_id)
    except QuotaExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    service = ChatService(db)
    try:
        result = service.chat(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            question=payload.question,
            conversation_id=payload.conversation_id,
            document_id=payload.document_id,
            n_context_chunks=payload.n_context_chunks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.CHAT_QUERY,
        resource_type="conversation",
        resource_id=result["conversation_id"],
        ip_address=request.client.host if request.client else None,
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


@router.get("/", response_model=ConversationListResponse)
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationListResponse:
    """List all conversations for the current user."""
    service = ChatService(db)
    conversations = service.list_conversations(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    return ConversationListResponse(
        conversations=[ConversationSummary(**c) for c in conversations],
        total=len(conversations),
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete an entire conversation (GDPR right to erasure)."""
    service = ChatService(db)
    count = service.delete_conversation(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.CHAT_DELETE,
        resource_type="conversation",
        resource_id=conversation_id,
    )


# ── WebSocket streaming chat ──────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_chat(ws: WebSocket) -> None:
    """WebSocket endpoint for streaming RAG responses token-by-token.

    Connection:
        ws://host/api/v1/chat/ws?token=<JWT>

    Send JSON: {"question": "...", "conversation_id": "...", "document_id": "..."}
    Receive JSON frames: {"type": "token", "content": "..."} or {"type": "done"}
    """
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4001, reason="Missing authentication token")
        return

    try:
        claims = decode_access_token(token)
    except TokenPayloadError:
        await ws.close(code=4001, reason="Invalid token")
        return

    from uuid import UUID
    user_id = UUID(claims["sub"])
    tenant_id = UUID(claims["tenant_id"])

    await ws.accept()

    db = get_session_factory()()
    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "content": "Invalid JSON"})
                continue

            question = data.get("question", "")
            try:
                question = sanitize_chat_message(question, max_length=app_settings.chat_max_question_chars)
            except ValueError as exc:
                await ws.send_json({"type": "error", "content": str(exc)})
                continue

            service = ChatService(db)
            async for token_text in service.stream_chat(
                tenant_id=tenant_id,
                user_id=user_id,
                question=question,
                conversation_id=data.get("conversation_id"),
                document_id=UUID(data["document_id"]) if data.get("document_id") else None,
            ):
                await ws.send_json({"type": "token", "content": token_text})

            await ws.send_json({"type": "done"})
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected (user=%s)", user_id)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        await ws.close(code=1011, reason="Internal error")
    finally:
        db.close()
