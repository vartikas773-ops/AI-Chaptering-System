from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import db
from .config import CORS_ORIGINS, MEDIA_DIR
from .jobs import run_pipeline
from .models import SpotifyJobRequest, SpotifySearchRequest, YoutubeJobRequest
from .sources.spotify_listennotes import search_episodes
from .sources.upload import save_upload

app = FastAPI(title="TopicTrail API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    db.init_db()


# ---------------------------------------------------------------- root / health

@app.get("/")
def root():
    return {"status": "ok", "service": "TopicTrail API", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"ok": True}


# ---------------------------------------------------------------- jobs: create

@app.post("/api/jobs/upload")
async def create_upload_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = db.create_job(source_type="upload", source_ref=file.filename, title=file.filename)
    media_path = await save_upload(file, job_id)
    background_tasks.add_task(run_pipeline, job_id, "upload", file.filename, media_path)
    return {"job_id": job_id}


@app.post("/api/jobs/youtube")
def create_youtube_job(payload: YoutubeJobRequest, background_tasks: BackgroundTasks):
    job_id = db.create_job(source_type="youtube", source_ref=payload.url)
    background_tasks.add_task(run_pipeline, job_id, "youtube", payload.url)
    return {"job_id": job_id}


# ---------------------------------------------------------------- jobs: spotify (via ListenNotes)

@app.post("/api/spotify/search")
def spotify_search(payload: SpotifySearchRequest):
    """Search Spotify-style podcast episodes by name (proxied through ListenNotes)."""
    try:
        return {"results": search_episodes(payload.query, payload.limit)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(e)) from e


@app.post("/api/jobs/spotify")
def create_spotify_job(payload: SpotifyJobRequest, background_tasks: BackgroundTasks):
    job_id = db.create_job(source_type="spotify", source_ref=payload.episode_id)
    background_tasks.add_task(run_pipeline, job_id, "spotify", payload.episode_id)
    return {"job_id": job_id}


# ---------------------------------------------------------------- jobs: read/list/delete

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/jobs")
def list_jobs(limit: int = 50):
    return {"jobs": db.list_jobs(limit)}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("media_path"):
        Path(job["media_path"]).unlink(missing_ok=True)
    for p in MEDIA_DIR.glob(f"{job_id}*"):
        p.unlink(missing_ok=True)
    db.delete_job(job_id)
    return {"deleted": True}


# ---------------------------------------------------------------- media streaming

@app.get("/api/media/{job_id}")
def stream_media(job_id: str):
    job = db.get_job(job_id)
    if not job or not job.get("media_path"):
        raise HTTPException(status_code=404, detail="media not found")
    path = Path(job["media_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="media file missing on disk")
    return FileResponse(path)