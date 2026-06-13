"""YouTube URL parsing, metadata lookup, and transcript fetching."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Iterable, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen


_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class AskTubeError(Exception):
    """Base exception for user-facing AskTube errors."""


class InvalidYouTubeURLError(AskTubeError):
    """Raised when a URL does not contain a valid YouTube video id."""


class TranscriptUnavailableError(AskTubeError):
    """Raised when no transcript can be fetched for the video."""


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    duration: float
    text: str


@dataclass(frozen=True)
class VideoData:
    video_id: str
    title: str
    channel: str
    published: str
    canonical_url: str
    transcript: list[TranscriptSegment]


def parse_video_id(url: str) -> str:
    """Extract and validate the video id from common YouTube URL shapes."""
    if not url or not isinstance(url, str):
        raise InvalidYouTubeURLError("A YouTube URL is required.")

    candidate = url.strip()
    if _VIDEO_ID_RE.match(candidate):
        return candidate

    parsed = urlparse(candidate)
    if not parsed.scheme:
        parsed = urlparse("https://" + candidate)

    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("m."):
        host = host[2:]

    video_id = ""
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "music.youtube.com", "youtube-nocookie.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        else:
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2 and parts[0] in {"embed", "shorts", "live", "v"}:
                video_id = parts[1]

    if not _VIDEO_ID_RE.match(video_id):
        raise InvalidYouTubeURLError(f"Invalid or unsupported YouTube URL: {url}")
    return video_id


def canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def fetch_metadata(video_id: str, timeout: float = 5.0) -> dict[str, str]:
    """Fetch lightweight public metadata using YouTube oEmbed.

    oEmbed does not expose the publish date, so the field is intentionally
    returned as Unknown unless another source is added later.
    """
    url = "https://www.youtube.com/oembed?" + urlencode(
        {"url": canonical_url(video_id), "format": "json"}
    )
    fallback = {
        "title": f"YouTube video {video_id}",
        "channel": "Unknown",
        "published": "Unknown",
    }
    try:
        with urlopen(url, timeout=timeout) as response:  # nosec B310 - fixed oEmbed host
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return fallback

    return {
        "title": str(data.get("title") or fallback["title"]),
        "channel": str(data.get("author_name") or fallback["channel"]),
        "published": fallback["published"],
    }


def _coerce_segment(raw: object) -> TranscriptSegment:
    if isinstance(raw, dict):
        text = raw.get("text", "")
        start = raw.get("start", 0.0)
        duration = raw.get("duration", 0.0)
    else:
        text = getattr(raw, "text", "")
        start = getattr(raw, "start", 0.0)
        duration = getattr(raw, "duration", 0.0)

    cleaned = " ".join(str(text).replace("\n", " ").split())
    return TranscriptSegment(start=float(start), duration=float(duration), text=cleaned)


def fetch_transcript(
    video_id: str,
    languages: Sequence[str] = ("en",),
) -> list[TranscriptSegment]:
    """Fetch a transcript with compatibility for old and new library APIs."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:  # pragma: no cover - installation issue
        raise TranscriptUnavailableError(
            "youtube-transcript-api is not installed. Run: pip install -e ."
        ) from exc

    raw_transcript: Iterable[object]
    try:
        api = YouTubeTranscriptApi()
        if hasattr(api, "fetch"):
            raw_transcript = api.fetch(video_id, languages=list(languages))
        elif hasattr(YouTubeTranscriptApi, "get_transcript"):
            raw_transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=list(languages)
            )
        else:  # pragma: no cover - defensive for unexpected future APIs
            raw_transcript = YouTubeTranscriptApi.list_transcripts(video_id).find_transcript(
                list(languages)
            ).fetch()
    except Exception as exc:  # noqa: BLE001 - normalize third-party exceptions
        raise TranscriptUnavailableError(
            f"No transcript is available for video {video_id}."
        ) from exc

    segments = [_coerce_segment(item) for item in raw_transcript]
    segments = [segment for segment in segments if segment.text]
    if not segments:
        raise TranscriptUnavailableError(f"Transcript for {video_id} is empty.")
    return segments


def fetch_video(url: str) -> VideoData:
    video_id = parse_video_id(url)
    metadata = fetch_metadata(video_id)
    return VideoData(
        video_id=video_id,
        title=metadata["title"],
        channel=metadata["channel"],
        published=metadata["published"],
        canonical_url=canonical_url(video_id),
        transcript=fetch_transcript(video_id),
    )
