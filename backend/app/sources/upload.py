"""
Local file upload ingestion (audio or video -- ffmpeg/librosa handle the demux).
"""
from pathlib import Path

from fastapi import UploadFile

from ..config import MEDIA_DIR


async def save_upload(file: UploadFile, job_id: str) -> Path:
    suffix = Path(file.filename or "upload.bin").suffix or ".bin"
    dest = MEDIA_DIR / f"{job_id}{suffix}"
    with open(dest, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)
    return dest
