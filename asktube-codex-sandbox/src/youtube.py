"""YouTube URL parsing and transcript retrieval."""

from dataclasses import dataclass
import json
from typing import Any, Callable, Iterable
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


class YouTubeError(Exception):
    """Base error for YouTube operations."""


class InvalidYouTubeURL(YouTubeError):
    """Raised when a URL does not identify a YouTube video."""


class TranscriptUnavailable(YouTubeError):
    """Raised when captions cannot be fetched."""


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start: float
    duration: float


@dataclass(frozen=True)
class Video:
    video_id: str
    title: str
    channel: str
    published: str
    canonical_url: str
    transcript: tuple[TranscriptSegment, ...]


def parse_video_id(url: str) -> str:
    """Extract an 11-character video ID from a standard YouTube URL."""
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise InvalidYouTubeURL("Please provide a valid YouTube URL.") from exc

    host = (parsed.hostname or "").lower()
    video_id = ""
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            video_id = parsed.path.split("/")[2]
    elif host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if len(video_id) != 11 or not set(video_id) <= allowed:
        raise InvalidYouTubeURL("Please provide a valid YouTube URL.")
    return video_id


def _default_metadata_fetcher(canonical_url: str) -> dict[str, Any]:
    query = urlencode({"url": canonical_url, "format": "json"})
    request = Request(
        f"https://www.youtube.com/oembed?{query}",
        headers={"User-Agent": "asktube/0.1"},
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def _default_transcript_api() -> Any:
    from youtube_transcript_api import YouTubeTranscriptApi

    return YouTubeTranscriptApi()


def _normalize_segments(raw_segments: Iterable[Any]) -> tuple[TranscriptSegment, ...]:
    normalized = []
    for segment in raw_segments:
        if isinstance(segment, dict):
            text = segment["text"]
            start = segment["start"]
            duration = segment.get("duration", 0)
        else:
            text = segment.text
            start = segment.start
            duration = segment.duration
        normalized.append(TranscriptSegment(str(text), float(start), float(duration)))
    return tuple(normalized)


def fetch_video(
    url: str,
    *,
    transcript_api: Any = None,
    metadata_fetcher: Callable[[str], dict[str, Any]] = _default_metadata_fetcher,
) -> Video:
    """Fetch captions and free public metadata for a YouTube video."""
    video_id = parse_video_id(url)
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    api = transcript_api or _default_transcript_api()

    try:
        if hasattr(api, "fetch"):
            raw_transcript = api.fetch(video_id)
        else:
            # youtube-transcript-api versions before 1.0 exposed get_transcript.
            raw_transcript = api.get_transcript(video_id)
        transcript = _normalize_segments(raw_transcript)
        if not transcript:
            raise RuntimeError("empty transcript")
    except Exception as exc:
        raise TranscriptUnavailable(
            f"Transcript unavailable for video {video_id}: {exc}"
        ) from exc

    # NOTE: oEmbed exposes title/channel but not publish date, so it remains Unknown.
    try:
        metadata = metadata_fetcher(canonical_url)
    except Exception:
        metadata = {}

    return Video(
        video_id=video_id,
        title=str(metadata.get("title") or "Unknown"),
        channel=str(metadata.get("author_name") or "Unknown"),
        published="Unknown",
        canonical_url=canonical_url,
        transcript=transcript,
    )
