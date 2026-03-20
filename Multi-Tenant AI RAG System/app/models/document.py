"""
Document and DocumentChunk SQLAlchemy models.
Represents uploaded PDFs and their processed chunks for RAG.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.db.database import Base


class DocumentStatus(str, enum.Enum):
    """Status of document processing pipeline."""
    UPLOADED = "uploaded"      # Just uploaded, awaiting processing
    PROCESSING = "processing"  # Being chunked & embedded
    COMPLETED = "completed"    # Ready for RAG queries
    FAILED = "failed"           # Processing errored out


class Document(Base):
    """
    Represents a PDF document uploaded by a user.
    
    WHY this design:
    - tenant_id ensures strict isolation (core security requirement)
    - Status enum tracks processing state (critical for async operations in Phase 4)
    - file_path can be local or S3 URL (future-proof for cloud storage)
    - total_chunks pre-computed for efficient pagination
    - Relationships to User & Tenant ensure data consistency
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    uploaded_by_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # File metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Processing status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    content_preview = Column(Text, nullable=True)
    
    # Processing metrics
    total_chunks = Column(Integer, default=0, nullable=False)
    embedding_model = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    uploaded_by_user = relationship("User", back_populates="documents", foreign_keys=[uploaded_by_id])
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, tenant_id={self.tenant_id}, status={self.status})>"


class DocumentChunk(Base):
    """
    Represents a chunk of a document (for RAG queries).
    
    WHY this design:
    - Separate table allows efficient filtering by tenant + document in Phase 5
    - Vectors live in ChromaDB/Pinecone (not in SQL), but ID stored here for reference
    - chunk_index preserves document order (important for context in RAG)
    - tenant_id denormalized for fast filtering (optimization for RAG queries)
    """
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("documents.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding_id = Column(String(255), nullable=True)  # ID in ChromaDB/Pinecone
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
