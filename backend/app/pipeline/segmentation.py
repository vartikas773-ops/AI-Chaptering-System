"""
Topic segmentation: embedding-based sliding window + cosine similarity,
using SentenceTransformers' all-MiniLM-L6-v2 -- the same approach and same
model as embedding_segmentation.py in the reference project, which she
found to significantly outperform a lexical/TF-IDF baseline (vocabulary
can shift while the topic stays the same, and vice versa).

Returns a list of sentence-index boundaries, which the caller turns into
(start_time, end_time, text) chapter spans.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import SBERT_BOUNDARY_PERCENTILE, SBERT_MODEL, SBERT_WINDOW

_sbert_cache: dict[str, SentenceTransformer] = {}


def _get_sbert(model_name: str = SBERT_MODEL) -> SentenceTransformer:
    if model_name not in _sbert_cache:
        _sbert_cache[model_name] = SentenceTransformer(model_name)
    return _sbert_cache[model_name]


def segment(
    sentences: list[str],
    window: int = SBERT_WINDOW,
    boundary_percentile: float = SBERT_BOUNDARY_PERCENTILE,
) -> list[int]:
    """
    Embed each sentence, compare the mean embedding of the `window`
    sentences before vs. after each gap, and call a boundary wherever
    similarity drops into the lowest percentile.
    """
    if len(sentences) < (2 * window + 2):
        return [0]

    model = _get_sbert()
    embeddings = model.encode(sentences, show_progress_bar=False)

    scores = []
    for i in range(window, len(sentences) - window):
        left = embeddings[i - window: i].mean(axis=0, keepdims=True)
        right = embeddings[i: i + window].mean(axis=0, keepdims=True)
        sim = cosine_similarity(left, right)[0][0]
        scores.append((i, sim))

    if not scores:
        return [0]

    sims = np.array([s for _, s in scores])
    threshold = np.percentile(sims, boundary_percentile)

    boundaries = [0]
    for i, sim in scores:
        if sim <= threshold:
            boundaries.append(i)

    # collapse boundaries that fall within `window` sentences of each other
    collapsed = [boundaries[0]]
    for b in boundaries[1:]:
        if b - collapsed[-1] >= window:
            collapsed.append(b)
    return collapsed
