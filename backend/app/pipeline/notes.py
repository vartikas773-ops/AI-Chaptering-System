"""
AI Notes: summary, per-chapter key points, topics and action items.

Runs fully locally on models the pipeline already loads -- no new
dependencies and no API keys:
  - Summaries:    the distilBART summarizer from chaptering.py (TITLING_MODEL)
  - Key points:   the sentences closest to each chapter's mean SBERT embedding
                  (segmentation.py's all-MiniLM-L6-v2), i.e. the most
                  representative lines
  - Action items: phrase detection on commitments/instructions ("we need to",
                  "make sure", "don't forget", ...)

Input is exactly what the rest of the pipeline already produces:
  chapters  = chaptering.build_chapters(...)
  sentences = transcription.transcribe_chunks(...)
"""
import re

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .chaptering import _get_titler
from .segmentation import _get_sbert

SUMMARY_CHUNK_WORDS = 500
MAX_SUMMARY_CHUNKS = 3
KEY_POINTS_PER_CHAPTER = 3
MAX_ACTION_ITEMS = 10

_ACTION = re.compile(
    r"\b(we need to|you need to|i need to|we should|you should|let'?s|make sure|"
    r"don'?t forget|remember to|follow up|next step|action item|have to|"
    r"i'?ll|we'?ll|reach out|take a look at|sign up|set up)\b",
    re.I,
)


def _summarize(text: str, max_len: int = 60, min_len: int = 15) -> str:
    """Summarize text of any length by chunking, since distilBART reads ~1k tokens."""
    words = text.split()
    if len(words) < 40:
        return ""
    chunks = [" ".join(words[i : i + SUMMARY_CHUNK_WORDS]) for i in range(0, len(words), SUMMARY_CHUNK_WORDS)]
    if len(chunks) > MAX_SUMMARY_CHUNKS:  # evenly spaced sample so long chapters stay covered
        idx = np.linspace(0, len(chunks) - 1, MAX_SUMMARY_CHUNKS).round().astype(int)
        chunks = [chunks[i] for i in idx]
    try:
        titler = _get_titler()
        parts = [
            titler(c, max_length=max_len, min_length=min_len, do_sample=False, truncation=True)[0]["summary_text"].strip()
            for c in chunks
        ]
        return " ".join(parts)
    except Exception:
        return ""


def _key_sentences(sents: list[dict], k: int = KEY_POINTS_PER_CHAPTER) -> list[str]:
    cand = [s for s in sents if 7 <= len(s["text"].split()) <= 45]
    if len(cand) <= k:
        return [s["text"].strip() for s in cand]
    emb = _get_sbert().encode([s["text"] for s in cand], show_progress_bar=False)
    scores = cosine_similarity(emb, emb.mean(axis=0, keepdims=True))[:, 0]
    top = sorted(np.argsort(scores)[::-1][:k])  # keep original order
    return [cand[i]["text"].strip() for i in top]


def _action_items(sentences: list[dict]) -> list[dict]:
    hits = []
    for s in sentences:
        n = len(s["text"].split())
        if 5 <= n <= 40 and _ACTION.search(s["text"]):
            hits.append({"start": s["start"], "text": s["text"].strip()})
    if len(hits) > MAX_ACTION_ITEMS:  # spread across the episode rather than only the first ones
        idx = np.linspace(0, len(hits) - 1, MAX_ACTION_ITEMS).round().astype(int)
        hits = [hits[i] for i in idx]
    return hits


def build_notes(chapters: list[dict], sentences: list[dict]) -> dict:
    visible = [c for c in chapters if not c.get("is_micro")] or chapters

    key_points = []
    for ch in visible:
        # assign sentences to a chapter by their midpoint on the timeline
        own = [s for s in sentences if ch["start"] <= (s["start"] + s["end"]) / 2 < ch["end"]]
        key_points.append(
            {
                "chapter_index": ch["index"],
                "start": ch["start"],
                "end": ch["end"],
                "title": ch["title"],
                "summary": _summarize(ch["text"]),
                "points": _key_sentences(own),
                "keywords": ch["keywords"],
                "sentiment": ch["sentiment"],
            }
        )

    # overall summary = summary of the chapter summaries
    joined = " ".join(k["summary"] for k in key_points if k["summary"])
    overall = _summarize(joined, max_len=90, min_len=30) if len(joined.split()) > 80 else joined

    counts: dict[str, int] = {}
    for ch in visible:
        for kw in ch["keywords"]:
            counts[kw] = counts.get(kw, 0) + 1
    topics = [k for k, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:8]]

    return {
        "summary": overall,
        "topics": topics,
        "key_points": key_points,
        "action_items": _action_items(sentences),
    }
