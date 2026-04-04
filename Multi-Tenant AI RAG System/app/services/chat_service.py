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
from app.utils.metrics import CHAT_CONTEXT_CHUNKS_USED, CHAT_REQUESTS_TOTAL, CHAT_RESPONSE_DURATION
from app.utils.sanitize import sanitize_chat_message
from app.utils.tracing import trace_span

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


def _has_valid_anthropic_key() -> bool:
    key = settings.anthropic_api_key
    return bool(key and key.startswith("sk-ant-") and len(key) > 20)


def _get_llm_provider() -> str:
    """Return the best available LLM provider."""
    if _has_valid_anthropic_key():
        return "anthropic"
    if _has_valid_openai_key():
        return "openai"
    return "fallback"


def _call_anthropic(question: str, context: str, history: list[dict]) -> str:
    """Call Anthropic Claude API with retry and exponential backoff."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    messages = []
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    user_message = f"""Context from documents:
---
{context}
---

Question: {question}"""
    messages.append({"role": "user", "content": user_message})

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                system=_SYSTEM_PROMPT,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return response.content[0].text or "No response generated."
        except (anthropic.APIConnectionError, anthropic.APITimeoutError, anthropic.RateLimitError) as exc:
            last_exc = exc
            delay = _RETRY_BASE_DELAY * (2 ** attempt)
            logger.warning("Anthropic API error (attempt %d/%d): %s — retrying in %.1fs", attempt + 1, _MAX_RETRIES, exc, delay)
            time.sleep(delay)
        except Exception as exc:
            logger.error("Anthropic non-retryable error: %s", exc)
            return f"AI generation failed: {type(exc).__name__}. Showing document context instead.\n\n{context}"

    logger.error("Anthropic API failed after %d retries: %s", _MAX_RETRIES, last_exc)
    return f"AI service temporarily unavailable. Showing document context instead.\n\n{context}"


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
        f"_Note: Configure ANTHROPIC_API_KEY or OPENAI_API_KEY for AI-generated answers._"
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
        start = time.time()

        # Sanitize and validate question
        question = sanitize_chat_message(question, max_length=settings.chat_max_question_chars)

        # Generate or reuse conversation ID
        if not conversation_id:
            conversation_id = str(uuid_mod.uuid4())

        with trace_span("chat.query", {"tenant.id": str(tenant_id), "conversation.id": conversation_id}) as span:
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
            provider = _get_llm_provider()
            if provider == "anthropic":
                logger.info("Using Anthropic Claude for RAG response")
                answer = _call_anthropic(question, context, history)
            elif provider == "openai":
                logger.info("Using OpenAI for RAG response")
                answer = _call_openai(question, context, history)
            else:
                logger.info("No LLM key — using fallback context response")
                answer = _fallback_response(question, context)

            if span:
                span.set_attribute("chat.mode", provider)
                span.set_attribute("chat.context_chunks", len(chunks))

            # 4. Save messages to history
            self._save_message(tenant_id, user_id, conversation_id, MessageRole.USER, question)
            self._save_message(tenant_id, user_id, conversation_id, MessageRole.ASSISTANT, answer)

        CHAT_RESPONSE_DURATION.observe(time.time() - start)
        CHAT_CONTEXT_CHUNKS_USED.observe(len(chunks))
        CHAT_REQUESTS_TOTAL.labels(mode=provider).inc()

        return {
            "answer": answer,
            "conversation_id": conversation_id,
            "sources": chunks,
        }

    def list_conversations(
        self,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Return a paginated list of conversations with their last message timestamp.

        Uses a correlated subquery for the preview to avoid N+1 queries.
        Returns a tuple of (conversations, total_count).
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

        base_query = (
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
        )

        # Total distinct conversations before pagination
        total = base_query.count()

        rows = (
            base_query
            .order_by(func.max(ChatMessage.created_at).desc())
            .offset(skip)
            .limit(limit)
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
        return result, total

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
        # Sanitize and validate question
        question = sanitize_chat_message(question, max_length=settings.chat_max_question_chars)

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

        provider = _get_llm_provider()
        if provider == "anthropic":
            full_answer = ""
            async for token in _stream_anthropic(question, context, history):
                full_answer += token
                yield token
            self._save_message(tenant_id, user_id, conversation_id, MessageRole.ASSISTANT, full_answer)
        elif provider == "openai":
            full_answer = ""
            async for token in _stream_openai(question, context, history):
                full_answer += token
                yield token
            self._save_message(tenant_id, user_id, conversation_id, MessageRole.ASSISTANT, full_answer)
        else:
            answer = _fallback_response(question, context)
            self._save_message(tenant_id, user_id, conversation_id, MessageRole.ASSISTANT, answer)
            yield answer


async def _stream_anthropic(question: str, context: str, history: list[dict]) -> AsyncGenerator[str, None]:
    """Stream tokens from Anthropic Claude API."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    messages = []
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": f"Context from documents:\n---\n{context}\n---\n\nQuestion: {question}",
    })

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            system=_SYSTEM_PROMPT,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as exc:
        logger.error("Anthropic streaming error: %s", exc)
        yield f"AI generation failed: {type(exc).__name__}. Showing context instead.\n\n{context}"


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
