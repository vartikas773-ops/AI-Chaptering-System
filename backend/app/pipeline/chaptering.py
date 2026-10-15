"""
Turns raw (sentences, boundaries) into titled, keyworded, sentiment-scored
chapters.

  - Titles:    KeyBERT (a short keyphrase) refined into a headline by a
               distilBART summarizer, per the project brief.
  - Keywords:  TF-IDF across chapters (reference project's approach) --
               picks terms that are distinctive to *this* chapter versus
               the rest of the episode, then drops conversational filler.
  - Sentiment: VADER (same lib the reference project used) per chapter.
  - Quality filters ported from the reference project's user-feedback
    fixes: chapters under MICRO_SEGMENT_MIN_WORDS words are flagged
    `is_micro` so the frontend can hide them from Next/Prev navigation
    without deleting the data, and a small stopword list strips
    conversational noise ("yeah", "oh", "thing"...) from keywords/titles.
"""
import re

from keybert import KeyBERT
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline as hf_pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ..config import EXTRA_STOPWORDS, KEYBERT_MODEL, MICRO_SEGMENT_MIN_WORDS, TITLING_MODEL

_keybert = None
_titler = None
_vader = None


def _get_keybert() -> KeyBERT:
    global _keybert
    if _keybert is None:
        _keybert = KeyBERT(model=KEYBERT_MODEL)
    return _keybert


def _get_titler():
    global _titler
    if _titler is None:
        _titler = hf_pipeline("summarization", model=TITLING_MODEL)
    return _titler


def _get_vader() -> SentimentIntensityAnalyzer:
    global _vader
    if _vader is None:
        _vader = SentimentIntensityAnalyzer()
    return _vader


def _clean_terms(terms: list[str]) -> list[str]:
    out = []
    for t in terms:
        t = t.lower().strip()
        if t and t not in EXTRA_STOPWORDS and len(t) > 2:
            out.append(t)
    return out


def _make_title(text: str) -> str:
    kb = _get_keybert()
    keyphrases = kb.extract_keywords(text, keyphrase_ngram_range=(1, 3), stop_words="english", top_n=1)
    seed = keyphrases[0][0] if keyphrases else text[:60]

    words = text.split()
    if len(words) < 25:
        # too short for the summarizer to do anything useful with -- title from the seed phrase
        return seed.title()

    try:
        titler = _get_titler()
        out = titler(text, max_length=14, min_length=4, do_sample=False)
        title = out[0]["summary_text"].strip().rstrip(".")
        return title if title else seed.title()
    except Exception:
        return seed.title()


def _tfidf_keywords(chapter_texts: list[str], top_n: int = 6) -> list[list[str]]:
    """Per-chapter distinctive keywords vs. the rest of the episode (TF-IDF)."""
    if len(chapter_texts) < 2:
        vec = TfidfVectorizer(stop_words="english", max_features=50)
        try:
            matrix = vec.fit_transform(chapter_texts)
            terms = vec.get_feature_names_out()
            row = matrix.toarray()[0]
            top_idx = row.argsort()[::-1][:top_n]
            return [_clean_terms([terms[i] for i in top_idx if row[i] > 0])]
        except ValueError:
            return [[] for _ in chapter_texts]

    vec = TfidfVectorizer(stop_words="english", max_features=500)
    matrix = vec.fit_transform(chapter_texts)
    terms = vec.get_feature_names_out()
    all_keywords = []
    for row in matrix.toarray():
        top_idx = row.argsort()[::-1][:top_n]
        all_keywords.append(_clean_terms([terms[i] for i in top_idx if row[i] > 0]))
    return all_keywords


def _sentiment(text: str) -> dict:
    scores = _get_vader().polarity_scores(text)
    compound = scores["compound"]
    label = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
    return {"label": label, "compound": compound}


def build_chapters(sentences: list[dict], boundaries: list[int]) -> list[dict]:
    """
    sentences: list of {"start","end","text"} (from transcription.py)
    boundaries: sentence-index starts of each chapter (from segmentation.py)
    """
    bounds = sorted(set(boundaries) | {0, len(sentences)})
    spans = list(zip(bounds[:-1], bounds[1:]))

    chapter_texts = []
    for s, e in spans:
        chapter_texts.append(" ".join(re.sub(r"\s+", " ", sentences[i]["text"]).strip() for i in range(s, e)))

    keyword_sets = _tfidf_keywords(chapter_texts)

    chapters = []
    for idx, ((s, e), text, keywords) in enumerate(zip(spans, chapter_texts, keyword_sets)):
        word_count = len(text.split())
        chapters.append(
            {
                "index": idx,
                "start": sentences[s]["start"],
                "end": sentences[e - 1]["end"],
                "title": _make_title(text) if text.strip() else f"Chapter {idx + 1}",
                "text": text,
                "keywords": keywords,
                "sentiment": _sentiment(text),
                "word_count": word_count,
                "is_micro": word_count < MICRO_SEGMENT_MIN_WORDS,
            }
        )
    return chapters
