"""
Whisper transcription via faster-whisper (int8 CPU-friendly, per README).
Chunks are transcribed independently and their timestamps are offset back
into the original timeline, then flattened into one sentence-level list.
"""
from pathlib import Path

from faster_whisper import WhisperModel

from ..config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL

_model_cache: dict[str, WhisperModel] = {}


def _get_model(model_size: str = WHISPER_MODEL) -> WhisperModel:
    if model_size not in _model_cache:
        _model_cache[model_size] = WhisperModel(
            model_size, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
        )
    return _model_cache[model_size]


def transcribe_chunks(chunk_paths: list[Path], chunk_minutes: int = 10, model_size: str = WHISPER_MODEL) -> list[dict]:
    """
    Returns a flat list of {"start": float, "end": float, "text": str}
    sentence/segment dicts, offset-corrected across chunk boundaries.
    """
    model = _get_model(model_size)
    offset = 0.0
    all_segments: list[dict] = []

    for chunk_path in chunk_paths:
        segments, _info = model.transcribe(str(chunk_path), beam_size=5, vad_filter=True)
        for s in segments:
            all_segments.append(
                {"start": s.start + offset, "end": s.end + offset, "text": s.text.strip()}
            )
        # fixed-size chunks (preprocessing.chunk_audio), so a flat offset bump is correct
        # for every chunk except (harmlessly) the last one, which is never read again.
        offset += chunk_minutes * 60

    return all_segments
