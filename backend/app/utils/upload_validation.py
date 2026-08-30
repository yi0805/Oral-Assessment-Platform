"""Small, server-side validation helpers for files accepted by this app."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pdfplumber
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError


MAX_PDF_BYTES = 50 * 1024 * 1024
MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024
_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
_IMAGE_TYPES = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


async def _read_limited(file: UploadFile, maximum_bytes: int, oversize_detail: str) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > maximum_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=oversize_detail,
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def read_pdf_upload(file: UploadFile) -> bytes:
    """Read one PDF with an application-enforced 50 MB cap and parse check."""
    filename = file.filename or ""
    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=422, detail="Only PDF files are supported.")

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in _PDF_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail="Uploaded file must have a PDF content type.")

    payload = await _read_limited(file, MAX_PDF_BYTES, "PDF must be 50 MB or smaller.")
    if not payload:
        raise HTTPException(status_code=422, detail="The uploaded PDF is empty.")
    if not payload.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="Uploaded content is not a valid PDF.")

    try:
        with pdfplumber.open(BytesIO(payload)) as pdf:
            if not pdf.pages:
                raise ValueError("PDF has no pages")
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Uploaded content is not a readable PDF.") from exc

    return payload


async def read_profile_image(file: UploadFile) -> tuple[bytes, str, str]:
    """Return validated image bytes, canonical content type and extension."""
    declared_type = (file.content_type or "").lower()
    if declared_type not in {item[0] for item in _IMAGE_TYPES.values()}:
        raise HTTPException(status_code=422, detail="Profile picture must be JPEG, PNG, or WebP.")

    payload = await _read_limited(
        file, MAX_PROFILE_IMAGE_BYTES, "Profile picture must be 5 MB or smaller."
    )
    if not payload:
        raise HTTPException(status_code=422, detail="The uploaded image is empty.")
    try:
        with Image.open(BytesIO(payload)) as image:
            image.verify()
        with Image.open(BytesIO(payload)) as image:
            image_format = image.format or ""
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=422, detail="Uploaded image cannot be decoded.") from exc

    if image_format not in _IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="Profile picture must be JPEG, PNG, or WebP.")

    content_type, extension = _IMAGE_TYPES[image_format]
    if declared_type != content_type:
        raise HTTPException(status_code=422, detail="Image content type does not match its contents.")
    return payload, content_type, extension
