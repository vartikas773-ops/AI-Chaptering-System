"""
Audio preprocessing -- mirrors the reference project's approach:
LibROSA for loading/resampling, Pydub for silence trimming / loudness
normalization, standardized to 16kHz mono (what faster-whisper expects).
"""
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

TARGET_SR = 16000


def preprocess_audio(src_path: Path, job_id: str, out_dir: Path) -> Path:
    """
    Loads any audio/video file, trims leading/trailing silence, normalizes
    loudness, resamples to 16kHz mono, and writes a clean WAV that the
    rest of the pipeline (transcription) consumes.
    """
    # librosa can decode most containers ffmpeg supports (via audioread/soundfile)
    y, sr = librosa.load(str(src_path), sr=TARGET_SR, mono=True)

    # write to a temp wav so pydub (silence trimming + normalization) can work on it
    tmp_wav = out_dir / f"{job_id}_raw.wav"
    sf.write(tmp_wav, y, TARGET_SR)

    seg = AudioSegment.from_wav(tmp_wav)
    seg = seg.normalize()  # loudness normalization

    start_trim = detect_leading_silence(seg)
    end_trim = detect_leading_silence(seg.reverse())
    duration = len(seg)
    seg = seg[start_trim: duration - end_trim] if duration - end_trim > start_trim else seg

    clean_path = out_dir / f"{job_id}_clean.wav"
    seg.export(clean_path, format="wav")
    tmp_wav.unlink(missing_ok=True)

    return clean_path


def chunk_audio(clean_path: Path, out_dir: Path, job_id: str, chunk_minutes: int = 10) -> list[Path]:
    """
    Splits long audio into N-minute chunks so faster-whisper's memory stays
    bounded on long (2-3hr) podcasts, same strategy as the reference project.
    Returns chunk paths in order; caller stitches timestamps back together.
    """
    seg = AudioSegment.from_wav(clean_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    for i, start in enumerate(range(0, len(seg), chunk_ms)):
        piece = seg[start: start + chunk_ms]
        path = out_dir / f"{job_id}_chunk{i:03d}.wav"
        piece.export(path, format="wav")
        chunks.append(path)
    return chunks
