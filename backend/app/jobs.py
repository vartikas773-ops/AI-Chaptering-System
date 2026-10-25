"""
Background job orchestrator: wires ingestion -> preprocessing ->
transcription -> segmentation -> chaptering -> AI notes into one pipeline, updating
job status/progress in sqlite as it goes so the frontend can poll it.
"""
import traceback
from pathlib import Path

from . import db
from .config import MEDIA_DIR
from .pipeline.gemini_chaptering import build_chapters
from .pipeline.notes import build_notes
from .pipeline.preprocessing import chunk_audio, preprocess_audio
from .pipeline.transcription import transcribe_chunks
from .sources.spotify_listennotes import download_spotify_episode_audio
from .sources.youtube import download_youtube_audio
import subprocess

CHUNK_MINUTES = 10

def make_playable(path: Path) -> Path:
    if path.suffix.lower() in {".mp3", ".wav", ".m4a", ".mp4"}:
        return path
    out = path.with_suffix(".play.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path), "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-c:a", "aac", "-movflags", "+faststart", str(out)],
        check=True,
    )
    return out


def run_pipeline(job_id: str, source_type: str, source_ref: str, local_media_path: Path | None = None):
    try:
        # 1. Ingest -------------------------------------------------------
        db.update_job(job_id, status="downloading", progress=0.05)
        if source_type == "youtube":
            media_path, title = download_youtube_audio(source_ref, job_id)
        elif source_type == "spotify":
            media_path, title = download_spotify_episode_audio(source_ref, job_id)
        elif source_type == "upload":
            media_path, title = local_media_path, source_ref
        else:
            raise ValueError(f"Unknown source_type: {source_type}")

        play_path = make_playable(media_path)
        db.update_job(job_id, media_path=str(play_path), title=title, progress=0.15)

        # 2. Preprocess -----------------------------------------------------
        db.update_job(job_id, status="preprocessing", progress=0.2)
        clean_path = preprocess_audio(media_path, job_id, MEDIA_DIR)
        chunk_paths = chunk_audio(clean_path, MEDIA_DIR, job_id, chunk_minutes=CHUNK_MINUTES)

        # 3. Transcribe -------------------------------------------------------
        db.update_job(job_id, status="transcribing", progress=0.35)
        sentences, language = transcribe_chunks(chunk_paths, chunk_minutes=CHUNK_MINUTES)
        if not sentences:
            raise RuntimeError("Transcription produced no speech segments.")

        # 4. Chapter (boundaries + titles + keywords + sentiment, all via Gemini) ----
        db.update_job(job_id, status="titling", progress=0.7)
        chapters = build_chapters(sentences, language_hint=language)

        # 6. AI notes (best effort: a notes failure must not fail the whole job) -
        db.update_job(job_id, status="notes", progress=0.9)
        try:
            notes = build_notes(chapters, sentences)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            notes = None

        total_duration = sentences[-1]["end"]
        result = {
            "title": title,
            "media_url": f"/api/media/{job_id}",
            "total_duration_sec": total_duration,
            "chapters": chapters,
            "transcript": sentences,
            "notes": notes,
        }
        db.set_result(job_id, result)

        # tidy up intermediate chunk/raw files, keep the final playable media + clean wav
        for p in chunk_paths:
            Path(p).unlink(missing_ok=True)

    except Exception as e:  # noqa: BLE001 -- surface any pipeline failure to the UI
        db.update_job(job_id, status="error", error=f"{e}\n{traceback.format_exc()[-1500:]}")



