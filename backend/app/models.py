from pydantic import BaseModel, Field


class YoutubeJobRequest(BaseModel):
    url: str = Field(..., description="Any YouTube video/watch URL")


class SpotifySearchRequest(BaseModel):
    query: str = Field(..., description="Podcast or episode name to search on Spotify/ListenNotes")
    limit: int = 8


class SpotifyJobRequest(BaseModel):
    episode_id: str = Field(..., description="ListenNotes episode id returned by /api/spotify/search")


class Segment(BaseModel):
    index: int
    start: float
    end: float
    title: str
    text: str
    keywords: list[str]
    sentiment: dict  # {"label": "positive|neutral|negative", "compound": float}
    word_count: int
    is_micro: bool  # below MICRO_SEGMENT_MIN_WORDS -> hidden from nav by default
