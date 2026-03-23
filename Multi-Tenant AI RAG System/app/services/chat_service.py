"""
RAG Chat Service — retrieves relevant context and generates answers.
Supports OpenAI GPT when API key is configured, otherwise returns context-only responses.
"""

import logging
import uuid as uuid_mod
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


def _build_context_block(chunks: list[dict]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Source {i}]\n{chunk['text']}")
    return "\n\n".join(parts)


def _has_valid_openai_key() -> bool:
    key = settings.openai_api_key
    return bool(key and key.startswith("sk-") and "placeholder" not in key and len(key) > 20)


def _call_openai(question: str, context: str, history: list[dict]) -> str:
    """Call OpenAI ChatCompletion API."""
    from openai import OpenAI

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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )

    return response.choices[0].message.content or "No response generated."


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
