"""
Shared SentenceTransformers (all-MiniLM-L6-v2) loader.

The old percentile-threshold boundary detector that used to live here has been removed --
chaptering (boundaries, titles, keywords, sentiment) is now done entirely by Gemini, in
gemini_chaptering.py. This file now only holds the SBERT loader that notes.py still uses
to pick each chapter's most representative sentences for the AI Notes key-points list.
"""
from sentence_transformers import SentenceTransformer

from ..config import SBERT_MODEL

_sbert_cache: dict[str, SentenceTransformer] = {}


def _get_sbert(model_name: str = SBERT_MODEL) -> SentenceTransformer:
    if model_name not in _sbert_cache:
        _sbert_cache[model_name] = SentenceTransformer(model_name)
    return _sbert_cache[model_name]