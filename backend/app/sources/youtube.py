"""
YouTube ingestion via yt-dlp. Downloads video + audio (max 720p, H.264) as one mp4,
so the frontend can show the picture. The pipeline extracts the audio itself.
"""
from pathlib import Path

import yt_dlp

from ..config import MEDIA_DIR


def download_youtube_audio(url: str, job_id: str) -> tuple[Path, str]:
    """Returns (path_to_media_file, resolved_title). Now an mp4 with video."""
    ydl_opts = {
        "format": (
            "bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]"
            "/best[height<=720][ext=mp4]/best[height<=720]"
        ),
        "merge_output_format": "mp4",
        "outtmpl": str(MEDIA_DIR / f"{job_id}.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", url)

    media_path = MEDIA_DIR / f"{job_id}.mp4"
    if not media_path.exists():
        candidates = [p for p in MEDIA_DIR.glob(f"{job_id}.*") if p.suffix not in (".part", ".ytdl")]
        if not candidates:
            raise RuntimeError("yt-dlp did not produce an output file")
        media_path = candidates[0]

    return media_path, title
