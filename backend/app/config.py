"""
Central config. Everything is read from environment variables so nothing
secret ever gets hard-coded / committed.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_TIMEOUT_S = int(os.getenv("GEMINI_TIMEOUT_S", "120"))

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
MEDIA_DIR = STORAGE_DIR / "media"
DB_PATH = STORAGE_DIR / "topictrail.db"

MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# faster-whisper
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")   # "small" or "medium" per README
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

# segmentation (embedding sliding-window, the only method used)
SBERT_MODEL = os.getenv("SBERT_MODEL", "all-MiniLM-L6-v2")

# chapter titling
TITLING_MODEL = os.getenv("TITLING_MODEL", "sshleifer/distilbart-cnn-12-6")

# UI/quality filters (ported from the reference project's user-feedback fixes)
MICRO_SEGMENT_MIN_WORDS = int(os.getenv("MICRO_SEGMENT_MIN_WORDS", "15"))

# ListenNotes (used to resolve a Spotify/podcast episode to a fetchable audio URL)
LISTENNOTES_API_KEY = os.getenv("LISTENNOTES_API_KEY", "")
LISTENNOTES_BASE_URL = "https://listen-api.listennotes.com/api/v2"
# Use https://listen-api-test.listennotes.com/api/v2 with the mock key for free testing.

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5176,http://localhost:3000,http://localhost:8080",
).split(",")