"""
Spotify podcast ingestion.

Spotify's own streaming URLs are DRM-protected and cannot legally be
downloaded, so -- as instructed in the project brief -- we resolve the
episode through ListenNotes instead. ListenNotes indexes the same episode
from the podcast's public RSS feed and exposes a direct, non-DRM `audio`
enclosure URL for any episode that also has an open RSS feed (true for the
overwhelming majority of podcasts, including ones you find via Spotify;
it will NOT work for Spotify-exclusive/Spotify-Original shows that have no
public feed -- ListenNotes can't index audio that doesn't exist outside
Spotify's app, and neither can we).

Flow:
  1. /search?type=episode&q=...            -> pick a candidate episode
  2. /episodes/{id}                        -> resolve `audio` (mp3 URL) + title
  3. plain HTTP GET of that mp3 URL        -> save to storage/media
"""
from pathlib import Path

import httpx

from ..config import LISTENNOTES_API_KEY, LISTENNOTES_BASE_URL, MEDIA_DIR


def _headers() -> dict:
    if not LISTENNOTES_API_KEY:
        raise RuntimeError(
            "LISTENNOTES_API_KEY is not set. Get a free key at "
            "https://www.listennotes.com/api/ and set it as an env var."
        )
    return {"X-ListenAPI-Key": LISTENNOTES_API_KEY}


def search_episodes(query: str, limit: int = 8) -> list[dict]:
    """Search podcast episodes (the ones you'd normally find on Spotify) by name."""
    with httpx.Client(timeout=20) as client:
        resp = client.get(
            f"{LISTENNOTES_BASE_URL}/search",
            headers=_headers(),
            params={"q": query, "type": "episode", "len_min": 0, "len_max": 400, "page_size": limit},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "episode_id": item.get("id"),
                "title": item.get("title_original") or item.get("title"),
                "podcast_name": (item.get("podcast") or {}).get("title_original"),
                "publish_date": item.get("pub_date_ms"),
                "duration_sec": item.get("audio_length_sec"),
                "thumbnail": item.get("thumbnail") or item.get("image"),
                "listennotes_url": item.get("listennotes_url"),
            }
        )
    return results


def resolve_episode_audio(episode_id: str) -> dict:
    """Get the direct audio URL + metadata for one episode id."""
    with httpx.Client(timeout=20) as client:
        resp = client.get(f"{LISTENNOTES_BASE_URL}/episodes/{episode_id}", headers=_headers())
        resp.raise_for_status()
        data = resp.json()

    audio_url = data.get("audio")
    if not audio_url:
        raise RuntimeError(
            "ListenNotes has no direct audio URL for this episode "
            "(likely a Spotify-exclusive show with no public RSS feed)."
        )
    return {
        "audio_url": audio_url,
        "title": data.get("title"),
        "podcast_name": (data.get("podcast") or {}).get("title"),
    }


def download_spotify_episode_audio(episode_id: str, job_id: str) -> tuple[Path, str]:
    meta = resolve_episode_audio(episode_id)
    dest = MEDIA_DIR / f"{job_id}.mp3"
    with httpx.stream("GET", meta["audio_url"], timeout=60, follow_redirects=True) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
    title = meta["title"] or episode_id
    if meta.get("podcast_name"):
        title = f'{meta["podcast_name"]} - {title}'
    return dest, title
