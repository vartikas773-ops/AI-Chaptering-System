"""
YouTube ingestion via yt-dlp (same tool the original brief already listed).
Downloads best audio track only -> mp3, to keep the pipeline media-type agnostic.
"""
from pathlib import Path

import yt_dlp

from ..config import MEDIA_DIR


def download_youtube_audio(url: str, job_id: str) -> tuple[Path, str]:
    """Returns (path_to_audio_file, resolved_title)."""
    out_template = str(MEDIA_DIR / f"{job_id}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", url)

    audio_path = MEDIA_DIR / f"{job_id}.mp3"
    if not audio_path.exists():
        candidates = list(MEDIA_DIR.glob(f"{job_id}.*"))
        if not candidates:
            raise RuntimeError("yt-dlp did not produce an output file")
        audio_path = candidates[0]

    return audio_path, title
