"""
RAG Chat Service — retrieves relevant context and generates answers.
Supports OpenAI GPT when API key is configured, otherwise returns context-only responses.
"""

import logging
import time
import uuid as uuid_mod
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat import ChatMessage, MessageRole
from app.services.vector_store import search_chunks

logger = logging.getLogger(__name__)

# System prompt for RAG
_SYSTEM_PROMPT = """You are a helpful AI assistant for a document Q&A system.
Answer the user's question based ONLY on the provided context from their documents.
If the context doesn't contain enough information to answer, say so honestly.
Be concise and precise. Cite the relevant parts of the context when answering."""

# Retry settings for OpenAI API calls
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds, doubles each retry


def _build_context_block(chunks: list[dict]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Source {i}]\n{chunk['text']}")
    return "\n\n".join(parts)


def _has_valid_openai_key() -> bool:
    key = settings.openai_api_key
    return bool(key and key.startswith("sk-") and "placeholder" not in key and len(key) > 20)


def _call_openai(question: str, context: str, history: list[dict]) -> str:
    """Call OpenAI ChatCompletion API with retry and exponential backoff."""
    from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

    client = OpenAI(api_key=settings.openai_api_key)

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    # Add conversation history (last 10 messages for context window)
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current question with context
    user_message = f"""Context from documents:
---
{context}
---

Question: {question}"""

    messages.append({"role": "user", "content": user_message})

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content or "No response generated."
        except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
            last_exc = exc
            delay = _RETRY_BASE_DELAY * (2 ** attempt)
            logger.warning("OpenAI API error (attempt %d/%d): %s — retrying in %.1fs", attempt + 1, _MAX_RETRIES, exc, delay)
            time.sleep(delay)
        except Exception as exc:
            logger.error("OpenAI non-retryable error: %s", exc)
            return f"AI generation failed: {type(exc).__name__}. Showing document context instead.\n\n{context}"

    logger.error("OpenAI API failed after %d retries: %s", _MAX_RETRIES, last_exc)
    return f"AI service temporarily unavailable. Showing document context instead.\n\n{context}"


def _fallback_response(question: str, context: str) -> str:
    """Fallback when no OpenAI key — return context directly."""
    if not context.strip():
        return "No relevant documents found for your question."
    return (
        f"**Relevant context found for:** \"{question}\"\n\n"
        f"{context}\n\n"
        f"_Note: Configure OPENAI_API_KEY for AI-generated answers._"
    )


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def chat(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        question: str,
        conversation_id: str | None = None,
        document_id: UUID | None = None,
        n_context_chunks: int = 5,
    ) -> dict:
        """
        RAG pipeline:
        1. Search vector DB for relevant chunks
        2. Build context
        3. Generate answer (OpenAI or fallback)
        4. Store in conversation history
        """
        # Generate or reuse conversation ID
        if not conversation_id:
            conversation_id = str(uuid_mod.uuid4())

        # 1. Retrieve relevant chunks
        chunks = search_chunks(
            tenant_id=tenant_id,
            query=question,
            n_results=n_context_chunks,
            document_id=document_id,
        )

        context = _build_context_block(chunks) if chunks else ""

        # 2. Load conversation history
        history = self._get_history(tenant_id, user_id, conversation_id)

        # 3. Generate answer
        if _has_valid_openai_key():
            logger.info("Using OpenAI for RAG response")
            answer = _call_openai(question, context, history)
        else:
            logger.info("No OpenAI key — using fallback context response")
            answer = _fallback_response(question, context)

        # 4. Save messages to history
        self._save_message(tenant_id, user_id, conversation_id, MessageRole.USER, question)
        self._save_message(tenant_id, user_id, conversation_id, MessageRole.ASSISTANT, answer)

        return {
            "answer": answer,
            "conversation_id": conversation_id,
            "sources": chunks,
        }

    def list_conversations(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> list[dict]:
        """Return a list of conversations with their last message timestamp.

        Uses a correlated subquery for the preview to avoid N+1 queries.
        """
        from sqlalchemy import func, select
        from sqlalchemy.orm import aliased

        PreviewMsg = aliased(ChatMessage)
        preview_subq = (
            select(PreviewMsg.content)
            .where(
                PreviewMsg.conversation_id == ChatMessage.conversation_id,
                PreviewMsg.role == MessageRole.USER,
            )
            .order_by(PreviewMsg.created_at.asc())
            .limit(1)
            .correlate(ChatMessage)
            .scalar_subquery()
        )

        rows = (
            self.db.query(
                ChatMessage.conversation_id,
                func.count(ChatMessage.id).label("message_count"),
                func.min(ChatMessage.created_at).label("started_at"),
                func.max(ChatMessage.created_at).label("last_message_at"),
                preview_subq.label("preview"),
            )
            .filter(
                ChatMessage.tenant_id == tenant_id,
                ChatMessage.user_id == user_id,
            )
            .group_by(ChatMessage.conversation_id)
            .order_by(func.max(ChatMessage.created_at).desc())
            .all()
        )

        result = []
        for row in rows:
            preview = row.preview or ""
            result.append({
                "conversation_id": row.conversation_id,
                "message_count": row.message_count,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
                "preview": (preview[:100] + "...") if len(preview) > 100 else preview,
            })
        return result

    def get_conversation(
        self,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: str,
    ) -> list[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.tenant_id == tenant_id,
                ChatMessage.user_id == user_id,
                ChatMessage.conversation_id == conversation_id,
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    def delete_conversation(
        self,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: str,
    ) -> int:
        """Delete all messages in a conversation. Returns deleted count."""
        count = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.tenant_id == tenant_id,
                ChatMessage.user_id == user_id,
                ChatMessage.conversation_id == conversation_id,
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return count

    def _get_history(self, tenant_id: UUID, user_id: UUID, conversation_id: str) -> list[dict]:
        messages = self.get_conversation(tenant_id, user_id, conversation_id)
        return [{"role": m.role.value, "content": m.content} for m in messages]

    def _save_message(
        self,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: str,
        role: MessageRole,
        content: str,
    ) -> None:
        msg = ChatMessage(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.db.add(msg)
        self.db.commit()

    async def stream_chat(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        question: str,
        conversation_id: str | None = None,
        document_id: UUID | None = None,
        n_context_chunks: int = 5,
    ) -> AsyncGenerator[str, None]:
        """Stream a RAG response token-by-token. Falls back to non-streaming."""
        if not conversation_id:
            conversation_id = str(uuid_mod.uuid4())

        chunks = search_chunks(
            tenant_id=tenant_id,
            query=question,
            n_results=n_context_chunks,
            document_id=document_id,
        )
        context = _build_context_block(chunks) if chunks else ""
        history = self._get_history(tenant_id, user_id, conversation_id)

        self._save_message(tenant_id, user_id, conversation_id, MessageRole.USER, question)

        if _has_valid_openai_key():
            full_answer = ""
            async for token in _stream_openai(question, context, history):
                full_answer += token
                yield token
            self._save_message(tenant_id, user_id, conversation_id, MessageRole.ASSISTANT, full_answer)
        else:
            answer = _fallback_response(question, context)
            self._save_message(tenant_id, user_id, conversation_id, MessageRole.ASSISTANT, answer)
            yield answer


async def _stream_openai(question: str, context: str, history: list[dict]) -> AsyncGenerator[str, None]:
    """Stream tokens from OpenAI ChatCompletion API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": f"Context from documents:\n---\n{context}\n---\n\nQuestion: {question}",
    })

    try:
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as exc:
        logger.error("OpenAI streaming error: %s", exc)
        yield f"AI generation failed: {type(exc).__name__}. Showing context instead.\n\n{context}"
