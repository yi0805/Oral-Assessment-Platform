import asyncio
import logging
from io import BytesIO
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Material, MaterialChunk

from app.services import s3_client
from app.services.embedding_service import embed_batch

from app.utils.audio_transcriber import is_audio_extension, transcribe_audio_from_s3
from app.utils.pdf_extractor import extract_text_from_bytes
from app.utils.text_chunker import chunk_text

# 3-stage pipeline (after upload): EXTRACT → CHUNK → EMBED

logger = logging.getLogger(__name__)


def _get_db() -> Session:

    return SessionLocal()


def _run_async(coro):

    try:
        loop = asyncio.get_running_loop()

    except RuntimeError:
        return asyncio.run(coro)

    logger.warning("Running event loop detected in pipeline thread — using threadsafe dispatch")
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=180)


def _file_type_from_filename(filename: str) -> str:

    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""

def _extract_docx(file_bytes: bytes) -> tuple[str, int]:
    try:
        import docx  
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
# Public entry point
# ---------------------------------------------------------------------------


def run_pipeline(material_id: UUID) -> None:

    logger.info("Pipeline start for material %s", material_id)

    # Stage 1: Extract
    extracted_text = _stage_extract(material_id)
    if extracted_text is None:
        return

    # Stage 2: Chunk
    if not _stage_chunk(material_id, extracted_text):
        return

    # Stage 3: Embed
    _stage_embed(material_id)

    logger.info("Pipeline finished for material %s", material_id)


def _stage_extract(material_id: UUID) -> str | None:

    db = _get_db()

    try:
        material = db.query(Material).filter(Material.id == material_id).first()

        if not material:
            logger.error("Material %s not found during extraction", material_id)
            return None

        file_type = _file_type_from_filename(material.filename)

        # Audio files are transcribed directly from S3 (no local download needed)
        if is_audio_extension(file_type):
            try:
                result = transcribe_audio_from_s3(material.storage_key, file_type)
                extracted_text = result.text

            except Exception as exc:
                logger.error(
                    "Material %s: audio transcription error (%s): %s: %s",
                    material_id, file_type, type(exc).__name__, exc,
                )
                return None

            if not extracted_text or not extracted_text.strip():
                logger.error("Material %s: transcription returned empty text", material_id)
                return None

            logger.info(
                "Material %s: audio transcribed (%d chars)", material_id, len(extracted_text),
            )
            return extracted_text

        try:
            file_bytes = s3_client.download_file(material.storage_key)

        except FileNotFoundError:
            logger.error(
                "Material %s: file not found in storage: %s",
                material_id, material.storage_key,
            )
            return None

        except Exception as exc:
            logger.error("Material %s: storage download error: %s", material_id, exc)
            return None

        try:
            if file_type == "pdf":
                result = extract_text_from_bytes(file_bytes)
                extracted_text = result.text

            elif file_type == "txt":
                extracted_text = file_bytes.decode("utf-8", errors="replace")

            elif file_type == "docx":
                extracted_text, _ = _extract_docx(file_bytes)

            elif file_type == "pptx":
                extracted_text, _ = _extract_pptx(file_bytes)

            else:
                logger.error("Material %s: unsupported file type: %s", material_id, file_type)
                return None

        except Exception as exc:  
            logger.error(
                "Material %s: extraction error (%s): %s: %s",
                material_id, file_type, type(exc).__name__, exc,
            )
            return None

        if not extracted_text or not extracted_text.strip():
            logger.error("Material %s: extraction returned empty text", material_id)
            return None

        logger.info("Material %s: text extracted (%d chars)", material_id, len(extracted_text))

        return extracted_text

    except Exception as exc:  
        logger.exception("Unexpected error in _stage_extract for %s", material_id)
        return None
    
    finally:
        try:
            db.close()

        except Exception:  
            pass


def _stage_chunk(material_id: UUID, extracted_text: str) -> bool:

    db = _get_db()

    try:
        chunks = chunk_text(extracted_text, max_tokens=500, overlap_tokens=50)
        if not chunks:
            logger.error("Material %s: chunking produced zero chunks", material_id)
            return False

        db.execute(
            sa_text("DELETE FROM material_chunks WHERE material_id = :mid"),
            {"mid": str(material_id)},
        )

        for chunk in chunks:
            db.add(MaterialChunk(
                material_id=material_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
            ))

        db.commit()
        logger.info("Material %s: %d chunks saved", material_id, len(chunks))

    except Exception as exc: 
        logger.exception("Unexpected error in _stage_chunk for %s", material_id)
        return False
    
    finally:
        try:
            db.close()

        except Exception: 
            pass

    return True



def _stage_embed(material_id: UUID) -> None:

    db = _get_db()

    try:
        chunks = (
            db.query(MaterialChunk)
            .filter(MaterialChunk.material_id == material_id)
            .order_by(MaterialChunk.chunk_index.asc())
            .all()
        )

        if not chunks:
            logger.warning("Material %s: no chunks to embed", material_id)
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
            
        except Exception as exc:
            logger.warning(
                "Material %s: embedding failed (%s) — storing zero vectors. "
                "RAG will return no results for this material.",
                material_id, exc,
            )

            embeddings = [list(ZERO) for _ in chunks]

        for chunk, vec in zip(chunks, embeddings):
            chunk.embedding = vec

        db.commit()

        logger.info(
            "Material %s: pipeline complete — %d chunks embedded (768-dim Gemini)",
            material_id, len(chunks),
        )

    except Exception as exc:  
        logger.exception("Unexpected error in _stage_embed for %s", material_id)
    finally:
        try:
            db.close()
        except Exception: 
            pass
