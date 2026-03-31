"""
Material processing pipeline — the backbone of the system.

4-stage pipeline: UPLOAD → EXTRACT → CHUNK → EMBED → READY
Each stage updates materials.processing_status so progress is observable.
If extraction or chunking fails, status is set to 'failed'.
If embedding fails, the material is still marked 'ready' with a warning
(zero vectors) so the rest of the workflow is unblocked.

Design principles:
  - Each stage opens its own fresh DB session and closes it when done.
    No session state leaks between stages.
  - _set_status() always uses raw SQL with its own fresh session so a broken
    ORM session in a previous stage never prevents a status write.
  - Embed stage NEVER marks 'failed': on any error it stores zero vectors and
    marks 'ready' with a warning in processing_error.  RAG won't find the
    material until a real embed runs, but question generation still works.
"""
import asyncio
import logging
from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.material import Material, MaterialChunk
from app.services import s3_client
from app.services.embedding_service import embed_batch
from app.utils.pdf_extractor import extract_text_from_bytes
from app.utils.text_chunker import chunk_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_db() -> Session:
    """Return a fresh database session."""
    return SessionLocal()


def _set_status(
    material_id: UUID,
    status: str,
    error: str | None = None,
) -> None:
    """
    Write processing_status (and optionally processing_error) using a fresh
    raw-SQL session.  Never raises — failures are only logged.
    """
    db = _get_db()
    try:
        db.execute(
            sa_text(
                "UPDATE materials "
                "SET processing_status = :s, processing_error = :e "
                "WHERE id = :id"
            ),
            {"s": status, "e": error, "id": str(material_id)},
        )
        db.commit()
        suffix = f" [{error[:100]}]" if error else ""
        logger.info("Material %s → %s%s", material_id, status, suffix)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "CRITICAL: Cannot set status '%s' for material %s: %s",
            status, material_id, exc,
        )
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass


def _read_status(material_id: UUID) -> str | None:
    """Read current processing_status from DB.  Returns None if not found."""
    db = _get_db()
    try:
        row = db.execute(
            sa_text("SELECT processing_status FROM materials WHERE id = :id"),
            {"id": str(material_id)},
        ).fetchone()
        return row[0] if row else None
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass


def _run_async(coro):
    """
    Safely run an async coroutine from a synchronous background-task thread.

    FastAPI runs sync background tasks in a threadpool that has no event loop.
    asyncio.run() creates one. As a safety net we also handle the rare case
    where a loop already exists in the thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # normal case

    logger.warning("Running event loop detected in pipeline thread — using threadsafe dispatch")
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=180)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_pipeline(material_id: UUID) -> None:
    """
    Run (or resume) the full processing pipeline for a material.
    Called as a FastAPI BackgroundTask immediately after file upload.

    Stage 1 (UPLOAD) is already done by the route handler.
    This function handles stages 2–4: extract → chunk → embed.
    """
    current = _read_status(material_id)
    if current is None:
        logger.error("Pipeline: material %s not found in DB", material_id)
        return

    logger.info("Pipeline start for material %s (status: %s)", material_id, current)

    # Stage 2: Extract
    if current in ("uploaded", "failed"):
        if not _stage_extract(material_id):
            return  # status already set to 'failed'
        current = "chunking"

    # Stage 3: Chunk
    if current == "chunking":
        if not _stage_chunk(material_id):
            return  # status already set to 'failed'
        current = "embedding"

    # Stage 4: Embed  (always reaches 'ready', falls back to zero vectors)
    if current == "embedding":
        _stage_embed(material_id)

    logger.info("Pipeline finished for material %s", material_id)


# ---------------------------------------------------------------------------
# Stage 2: Extract
# ---------------------------------------------------------------------------

def _stage_extract(material_id: UUID) -> bool:
    """
    Download from storage and extract plain text from the file.
    Returns True on success; sets status='failed' and returns False on any error.
    """
    _set_status(material_id, "extracting")

    db = _get_db()
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            _set_status(material_id, "failed", "Material record not found during extraction")
            return False

        # Download from storage
        try:
            file_bytes = s3_client.download_file(material.storage_key)
        except FileNotFoundError:
            _set_status(
                material_id, "failed",
                f"File not found in storage: {material.storage_key}",
            )
            return False
        except Exception as exc:  # noqa: BLE001
            _set_status(material_id, "failed", f"Storage download error: {exc}")
            return False

        # Extract text based on file type
        file_type = (material.file_type or "").lower()
        try:
            if file_type == "pdf":
                result = extract_text_from_bytes(file_bytes)
                extracted_text = result.text
                page_count = result.page_count
                extraction_method = result.extraction_method

            elif file_type == "txt":
                extracted_text = file_bytes.decode("utf-8", errors="replace")
                page_count = 1
                extraction_method = "plain_text"

            elif file_type == "docx":
                extracted_text, page_count = _extract_docx(file_bytes)
                extraction_method = "python-docx"

            elif file_type == "pptx":
                extracted_text, page_count = _extract_pptx(file_bytes)
                extraction_method = "python-pptx"

            else:
                _set_status(
                    material_id, "failed",
                    f"Unsupported file type: {file_type}",
                )
                return False

        except Exception as exc:  # noqa: BLE001
            _set_status(
                material_id, "failed",
                f"Extraction error ({file_type}): {type(exc).__name__}: {exc}",
            )
            return False

        if not extracted_text or not extracted_text.strip():
            _set_status(material_id, "failed", "Extraction returned empty text")
            return False

        # Persist extracted text via this stage's own session
        material.extracted_text = extracted_text
        material.page_count = page_count
        material.extraction_method = extraction_method
        db.commit()

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error in _stage_extract for %s", material_id)
        _set_status(material_id, "failed", f"Unexpected extraction error: {exc}")
        return False
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass

    _set_status(material_id, "chunking")
    return True


def _extract_docx(file_bytes: bytes) -> tuple[str, int]:
    try:
        import docx  # python-docx
    except ImportError:
        raise RuntimeError("python-docx not installed. Run: pip install python-docx")

    doc = docx.Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
            if row_text:
                paragraphs.append(row_text)
    full_text = "\n\n".join(paragraphs)
    word_count = len(full_text.split())
    return full_text, max(1, round(word_count / 250))


def _extract_pptx(file_bytes: bytes) -> tuple[str, int]:
    try:
        from pptx import Presentation
    except ImportError:
        raise RuntimeError("python-pptx not installed. Run: pip install python-pptx")

    prs = Presentation(BytesIO(file_bytes))
    slides_text: list[str] = []
    for slide_no, slide in enumerate(prs.slides, start=1):
        parts = [
            para.text.strip()
            for shape in slide.shapes
            if shape.has_text_frame
            for para in shape.text_frame.paragraphs
            if para.text.strip()
        ]
        if parts:
            slides_text.append(f"[Slide {slide_no}]\n" + "\n".join(parts))
    return "\n\n".join(slides_text), len(prs.slides)


# ---------------------------------------------------------------------------
# Stage 3: Chunk
# ---------------------------------------------------------------------------

def _stage_chunk(material_id: UUID) -> bool:
    """
    Split extracted text into ~500-token chunks.
    Returns True on success; sets status='failed' and returns False on error.
    """
    db = _get_db()
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            _set_status(material_id, "failed", "Material not found during chunking")
            return False

        if not material.extracted_text or not material.extracted_text.strip():
            _set_status(material_id, "failed", "No extracted text to chunk")
            return False

        chunks = chunk_text(material.extracted_text, max_tokens=500, overlap_tokens=50)
        if not chunks:
            _set_status(material_id, "failed", "Chunking produced zero chunks")
            return False

        # Delete any stale chunks (idempotent)
        db.execute(
            sa_text("DELETE FROM material_chunks WHERE material_id = :mid"),
            {"mid": str(material_id)},
        )

        # Check whether the embedding column exists to pick the right INSERT strategy
        has_embed_col = _embedding_column_exists(db)

        if has_embed_col:
            for chunk in chunks:
                db.add(MaterialChunk(
                    material_id=material_id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    token_count=chunk.token_count,
                    source_page_start=chunk.source_page_start,
                    source_page_end=chunk.source_page_end,
                ))
        else:
            # Migration 002 not applied — skip the embedding column entirely
            logger.warning(
                "Material %s: 'embedding' column missing, using raw INSERT "
                "(run migration 002 to enable RAG search)",
                material_id,
            )
            for chunk in chunks:
                db.execute(
                    sa_text(
                        "INSERT INTO material_chunks "
                        "(id, material_id, chunk_index, chunk_text, token_count, "
                        " source_page_start, source_page_end) "
                        "VALUES (gen_random_uuid(), :mid, :ci, :ct, :tc, :sps, :spe)"
                    ),
                    {
                        "mid": str(material_id),
                        "ci": chunk.chunk_index,
                        "ct": chunk.chunk_text,
                        "tc": chunk.token_count,
                        "sps": chunk.source_page_start,
                        "spe": chunk.source_page_end,
                    },
                )

        material.total_chunks = len(chunks)
        db.commit()
        logger.info("Material %s: %d chunks saved", material_id, len(chunks))

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error in _stage_chunk for %s", material_id)
        _set_status(material_id, "failed", f"Chunking error: {type(exc).__name__}: {exc}")
        return False
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass

    if not has_embed_col:
        # No embedding column → skip embed stage, go straight to ready
        _set_status(
            material_id, "ready",
            "Chunks saved without embeddings (migration 002 not applied). "
            "RAG search will return no results until embeddings are generated.",
        )
        return False  # False stops run_pipeline from entering _stage_embed

    _set_status(material_id, "embedding")
    return True


def _embedding_column_exists(db: Session) -> bool:
    """Return True if material_chunks.embedding column exists in the DB."""
    try:
        row = db.execute(
            sa_text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'material_chunks' AND column_name = 'embedding'"
            )
        ).fetchone()
        return row is not None
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Stage 4: Embed
# ---------------------------------------------------------------------------

def _stage_embed(material_id: UUID) -> None:
    """
    Generate 768-dim Gemini embeddings for every chunk.

    This stage NEVER marks 'failed'.  On any error it stores zero vectors and
    marks the material 'ready' with a warning so the workflow is unblocked.
    """
    db = _get_db()
    warning: str | None = None
    try:
        chunks = (
            db.query(MaterialChunk)
            .filter(MaterialChunk.material_id == material_id)
            .order_by(MaterialChunk.chunk_index.asc())
            .all()
        )

        if not chunks:
            logger.warning("Material %s: no chunks to embed, marking ready", material_id)
            _set_status(material_id, "ready", "No chunks found — material is empty")
            return

        texts = [c.chunk_text for c in chunks]
        ZERO = [0.0] * 768

        try:
            embeddings = _run_async(embed_batch(texts))
            if len(embeddings) != len(chunks):
                raise ValueError(
                    f"Embedding count mismatch: got {len(embeddings)}, "
                    f"expected {len(chunks)}"
                )
        except Exception as exc:  # noqa: BLE001
            # Fallback: zero vectors — material is still usable for non-RAG workflows
            logger.warning(
                "Material %s: embedding failed (%s) — storing zero vectors. "
                "RAG will return no results for this material.",
                material_id, exc,
            )
            embeddings = [list(ZERO) for _ in chunks]
            warning = f"Embedding failed (zero vectors stored): {type(exc).__name__}: {str(exc)[:200]}"

        for chunk, vec in zip(chunks, embeddings):
            chunk.embedding = vec

        db.execute(
            sa_text(
                "UPDATE materials SET processed_at = :ts WHERE id = :id"
            ),
            {"ts": datetime.now(timezone.utc).isoformat(), "id": str(material_id)},
        )
        db.commit()

        if warning:
            logger.warning("Material %s: marked ready with warning: %s", material_id, warning)
        else:
            logger.info(
                "Material %s: pipeline complete — %d chunks embedded (768-dim Gemini)",
                material_id, len(chunks),
            )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error in _stage_embed for %s", material_id)
        warning = f"Embed stage crash: {type(exc).__name__}: {str(exc)[:200]}"
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass

    _set_status(material_id, "ready", warning)
