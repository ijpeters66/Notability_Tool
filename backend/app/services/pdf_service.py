from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

from app.config import get_settings


async def validate_pdf(file: UploadFile) -> bytes:
    settings = get_settings()
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported.")

    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        limit_mb = settings.max_upload_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF must be {limit_mb} MB or less.",
        )

    try:
        from io import BytesIO

        PdfReader(BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is not a valid PDF.") from exc

    return contents


def save_pdf(contents: bytes, original_filename: str | None) -> Path:
    settings = get_settings()
    suffix = Path(original_filename or "upload.pdf").suffix.lower()
    if suffix != ".pdf":
        suffix = ".pdf"
    target = settings.upload_dir / f"{uuid4().hex}{suffix}"
    target.write_bytes(contents)
    return target
