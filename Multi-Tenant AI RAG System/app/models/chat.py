"""
ChatMessage SQLAlchemy model for conversation history.
"""

from datetime import datetime
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.db.database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(Base):
    """Stores conversation history per tenant/user for context."""
    __tablename__ = "chat_messages"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(String(255), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
