import logging

from pydantic import BaseModel, Field

from ..config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TIMEOUT_S, MICRO_SEGMENT_MIN_WORDS

log = logging.getLogger("topictrail.gemini_chaptering")

_MAX_WORDS_PER_SEGMENT = 120  # guards against one freak oversized Whisper segment bloating the prompt


class ChapterError(RuntimeError):
    """Raised whenever Gemini chaptering can't produce a usable result. The message is
    written to be shown directly in the job's error field."""


def _require_key() -> None:
    if not GEMINI_API_KEY:
        raise ChapterError(
            "GEMINI_API_KEY is not set. Chaptering runs entirely on Gemini now, so a key is "
            "required -- add it to backend/.env (free, no card, at https://aistudio.google.com/apikey) "
            "and restart the server."
        )


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class _Chapter(BaseModel):
    start_index: int = Field(description="Index of the first transcript line in this chapter")
    end_index: int = Field(description="Index of the last transcript line in this chapter (inclusive)")
    title: str = Field(description="A short, specific, real title -- not a list of keywords -- "
                                   "in the transcript's own language")
    summary: str = Field(description="One or two sentences on what is actually discussed, "
                                     "in the transcript's own language")
    keywords: list[str] = Field(description="4 to 6 distinctive terms or short phrases for this "
                                            "chapter, in the transcript's own language. No filler "
                                            "words (yeah, okay, right, ...) and no function words.")
    sentiment: str = Field(description='Overall tone of this chapter: "positive", "neutral", or "negative"')


class _Response(BaseModel):
    chapters: list[_Chapter]


def _build_prompt(lines: list[dict], language_hint: str | None) -> str:
    lang_line = (
        f"The transcript is in {language_hint}. Write every title, summary and keyword in that "
        "same language -- never translate to English."
        if language_hint else
        "Write every title, summary and keyword in the same language as the transcript."
    )
    header = [
        "You are chaptering a transcript (a podcast, video, lecture or meeting recording) for "
        "someone who wants to jump straight to the part they care about.",
        "",
        "The transcript below is numbered, one line per automatically-detected speech segment. "
        "These are raw speech-to-text segments, not necessarily full sentences -- a line can be a "
        "fragment, and a short back-and-forth can span several lines. Read through them and group "
        "the whole transcript into chapters at genuine topic changes.",
        "",
        "Rules:",
        "- Every line must belong to exactly one chapter. Chapters must be in order and cover the "
        "entire transcript with no gaps and no overlaps.",
        "- A chapter must represent a real, sustained topic -- not a single aside, a laugh, an ad "
        "read, a brief tangent, or a few lines of filler. Fold anything like that into the chapter "
        "it interrupts or follows. Do not create a chapter for it.",
        "- Prefer fewer, more substantial chapters over many small ones. If you are unsure whether "
        "something is a real topic change, it probably isn't -- keep it in the surrounding chapter.",
        "- title: a short, specific, real title someone would read -- a phrase or short sentence, "
        "never a bare list of keywords and never wrapped in quote marks.",
        "- summary: one or two sentences on what is actually discussed.",
        "- keywords: 4 to 6 distinctive terms specific to this chapter -- not generic words, not "
        "conversational filler (yeah, okay, right, you know, ...), not function words.",
        "- sentiment: the chapter's overall tone -- positive, neutral, or negative.",
        "",
        lang_line,
        "",
        "Transcript:",
    ]
    for i, s in enumerate(lines):
        text = " ".join(s["text"].split()[:_MAX_WORDS_PER_SEGMENT])
        header.append(f"[{i}] ({_fmt_time(s['start'])}) {text}")
    return "\n".join(header)


def _repair(chapters: list[_Chapter], n: int) -> list[_Chapter]:
    """matching the 'fold it into the surrounding chapter'
    instruction the prompt already gave. This is input sanitation, not a second chaptering
    method: it never changes *which* lines end up grouped together except to close gaps
    the model shouldn't have left."""
    chapters = sorted(chapters, key=lambda c: (c.start_index, c.end_index))
    fixed: list[_Chapter] = []
    cursor = 0
    for c in chapters:
        if cursor >= n:
            break
        start = cursor
        end = min(max(c.end_index, start), n - 1)
        c.start_index, c.end_index = start, end
        fixed.append(c)
        cursor = end + 1
    if not fixed:
        raise ChapterError("Gemini returned no usable chapters for this transcript.")
    fixed[-1].end_index = n - 1
    return fixed


def build_chapters(sentences: list[dict], language_hint: str | None = None) -> list[dict]:
    """sentences: [{"start","end","text"}, ...] from transcription.py, in order.
    Returns the same chapter dict shape the rest of the app (notes.py, the API, the
    frontend) already expects: index, start, end, title, text, keywords, sentiment
    ({"label","compound"}), word_count, is_micro."""
    _require_key()
    if not sentences:
        raise ChapterError("Transcription produced no speech segments to chapter.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = _build_prompt(sentences, language_hint)

    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_Response,
                temperature=0.3,
                http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_S * 1000),  # ms
            ),
        )
    except Exception as exc:  # noqa: BLE001 -- surface a clear, specific error either way
        raise ChapterError(f"Gemini chaptering failed ({exc.__class__.__name__}): {exc}") from exc

    parsed: _Response | None = getattr(resp, "parsed", None)
    if parsed is None or not parsed.chapters:
        raise ChapterError("Gemini returned an empty or unparsable response.")

    spans = _repair(parsed.chapters, len(sentences))

    chapters: list[dict] = []
    for idx, c in enumerate(spans):
        text = " ".join(sentences[i]["text"].strip() for i in range(c.start_index, c.end_index + 1))
        word_count = len(text.split())
        label = c.sentiment.strip().lower()
        if label not in ("positive", "neutral", "negative"):
            label = "neutral"
        chapters.append({
            "index": idx,
            "start": sentences[c.start_index]["start"],
            "end": sentences[c.end_index]["end"],
            "title": c.title.strip() or f"Chapter {idx + 1}",
            "text": text,
            "keywords": [k.strip() for k in c.keywords if k.strip()][:6],
            "sentiment": {"label": label, "compound": {"positive": 0.5, "neutral": 0.0, "negative": -0.5}[label]},
            "word_count": word_count,
            "is_micro": word_count < MICRO_SEGMENT_MIN_WORDS,  # informational now; Gemini is told not to create these
        })
    return chapters