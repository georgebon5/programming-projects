"""
Document processing pipeline: extract text → chunk → store in vector DB.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.chunker import chunk_text
from app.services.text_extractor import extract_text
from app.services.vector_store import store_chunks
from app.utils.exceptions import DocumentNotFound, DocumentProcessingError

logger = logging.getLogger(__name__)


class ProcessingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def process_document(self, document_id: UUID, tenant_id: UUID) -> Document:
        """
        Full processing pipeline for a single document:
        1. Extract text from file
        2. Chunk text
        3. Store chunks in SQL + ChromaDB
        4. Update document status
        """
        doc = (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.tenant_id == tenant_id)
            .first()
        )
        if not doc:
            raise DocumentNotFound("Document not found")

        if doc.status not in (DocumentStatus.UPLOADED, DocumentStatus.FAILED):
            raise DocumentProcessingError(
                f"Document cannot be processed (status: {doc.status.value})"
            )

        # Mark as processing
        doc.status = DocumentStatus.PROCESSING
        doc.error_message = None
        self.db.commit()

        try:
            # 1. Extract text
            logger.info("Extracting text from %s", doc.file_path)
            full_text = extract_text(doc.file_path)

            # 2. Chunk text
            logger.info("Chunking text (%d chars)", len(full_text))
            chunks = chunk_text(full_text)
            logger.info("Created %d chunks", len(chunks))

            # 3. Store in ChromaDB
            logger.info("Storing chunks in vector DB")
            embedding_ids = store_chunks(
                tenant_id=tenant_id,
                document_id=document_id,
                chunks=chunks,
            )

            # 4. Store chunks in SQL
            for i, (chunk_str, emb_id) in enumerate(zip(chunks, embedding_ids, strict=True)):
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    tenant_id=tenant_id,
                    text=chunk_str,
                    chunk_index=i,
                    embedding_id=emb_id,
                )
                self.db.add(db_chunk)

            # 5. Update document
            doc.status = DocumentStatus.COMPLETED
            doc.total_chunks = len(chunks)
            doc.content_preview = full_text[:500]
            doc.embedding_model = "chromadb-default"
            doc.processed_at = datetime.now(UTC).replace(tzinfo=None)

            self.db.commit()
            self.db.refresh(doc)
            logger.info("Document %s processed successfully (%d chunks)", document_id, len(chunks))
            return doc

        except Exception as exc:
            self.db.rollback()
            # Update document with error
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)[:1000]
            self.db.commit()
            logger.error("Document %s processing failed: %s", document_id, exc)
            raise DocumentProcessingError(str(exc)) from exc
