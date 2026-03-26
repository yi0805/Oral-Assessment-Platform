"""
Material processing pipeline — the backbone of the system.

4-stage pipeline: UPLOAD -> EXTRACT -> CHUNK -> EMBED -> READY
Each stage updates materials.processing_status so progress is observable.
If any stage fails, status is set to 'failed' with the error message.
The pipeline can be retried from the failed stage, not from scratch.

Pipeline design principles:
  - Idempotent: safe to retry
  - Observable: processing_status tracks current stage
  - Resumable: restarts from the failed stage
"""
import logging
import asyncio
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.material import Material, MaterialChunk
from app.services import s3_client
from app.services.embedding_service import embed_batch
from app.utils.pdf_extractor import extract_text_from_bytes
from app.utils.text_chunker import chunk_text

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    """Get a fresh database session for background tasks."""
    return SessionLocal()


def _update_status(db: Session, material: Material, status: str, error: str | None = None):
    """Update the processing status and optionally set an error message."""
    material.processing_status = status
    if error:
        material.processing_error = error
    db.commit()
    logger.info(f"Material {material.id}: status -> {status}" + (f" (error: {error})" if error else ""))


def run_pipeline(material_id: UUID) -> None:
    """
    Run the full processing pipeline for a material.
    Called as a background task after file upload.

    Stage 1 (UPLOAD) is already done by the route handler.
    This function handles stages 2-4.
    """
    db = _get_db()
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            logger.error(f"Material {material_id} not found")
            return

        # Determine which stage to start from (for retry support)
        status = material.processing_status
        if status in ("uploaded", "failed"):
            _stage_extract(db, material)
        if material.processing_status == "chunking":
            _stage_chunk(db, material)
        if material.processing_status == "embedding":
            _stage_embed(db, material)

    except Exception as e:
        logger.exception(f"Pipeline failed for material {material_id}")
        try:
            _update_status(db, material, "failed", str(e))
        except Exception:
            pass
    finally:
        db.close()


def _stage_extract(db: Session, material: Material) -> None:
    """Stage 2: Download from S3 and extract text."""
    _update_status(db, material, "extracting")

    try:
        file_bytes = s3_client.download_file(material.storage_key)
    except FileNotFoundError:
        _update_status(db, material, "failed", f"File not found in storage: {material.storage_key}")
        return

    if material.file_type == "pdf":
        result = extract_text_from_bytes(file_bytes)
        material.extracted_text = result.text
        material.page_count = result.page_count
        material.extraction_method = result.extraction_method
    elif material.file_type == "txt":
        material.extracted_text = file_bytes.decode("utf-8", errors="replace")
        material.page_count = 1
        material.extraction_method = "plain_text"
    else:
        _update_status(db, material, "failed", f"Unsupported file type for extraction: {material.file_type}")
        return

    if not material.extracted_text or not material.extracted_text.strip():
        _update_status(db, material, "failed", "Extraction returned empty text")
        return

    _update_status(db, material, "chunking")


def _stage_chunk(db: Session, material: Material) -> None:
    """Stage 3: Split extracted text into ~500-token chunks."""
    if not material.extracted_text:
        _update_status(db, material, "failed", "No extracted text to chunk")
        return

    chunks = chunk_text(material.extracted_text, max_tokens=500, overlap_tokens=50)

    if not chunks:
        _update_status(db, material, "failed", "Chunking produced zero chunks")
        return

    # Delete any existing chunks (for retry idempotency)
    db.query(MaterialChunk).filter(MaterialChunk.material_id == material.id).delete()

    for chunk in chunks:
        db_chunk = MaterialChunk(
            material_id=material.id,
            chunk_index=chunk.chunk_index,
            chunk_text=chunk.chunk_text,
            token_count=chunk.token_count,
            source_page_start=chunk.source_page_start,
            source_page_end=chunk.source_page_end,
        )
        db.add(db_chunk)

    material.total_chunks = len(chunks)
    db.commit()

    _update_status(db, material, "embedding")


def _stage_embed(db: Session, material: Material) -> None:
    """Stage 4: Generate vector embeddings for each chunk via OpenAI."""
    chunks = (
        db.query(MaterialChunk)
        .filter(MaterialChunk.material_id == material.id)
        .order_by(MaterialChunk.chunk_index.asc())
        .all()
    )

    if not chunks:
        _update_status(db, material, "failed", "No chunks to embed")
        return

    # Get all chunk texts for batch embedding
    texts = [c.chunk_text for c in chunks]

    # Run async embedding in a sync context (background task)
    try:
        embeddings = asyncio.run(embed_batch(texts))
    except Exception as e:
        _update_status(db, material, "failed", f"Embedding API error: {str(e)}")
        return

    # Store embeddings
    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding

    from datetime import datetime, timezone
    material.processed_at = datetime.now(timezone.utc)

    db.commit()
    _update_status(db, material, "ready")
    logger.info(f"Material {material.id}: pipeline complete — {len(chunks)} chunks embedded")
