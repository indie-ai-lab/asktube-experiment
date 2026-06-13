"""Markdown formatting for AskTube summaries."""

from __future__ import annotations

from html import escape
from typing import Iterable

from youtube import TranscriptSegment, VideoData


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _timestamp_url(canonical_url: str, seconds: float) -> str:
    return f"{canonical_url}&t={max(0, int(seconds))}s"


def _topic_from_text(text: str, limit: int = 90) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def pick_notable_timestamps(
    segments: Iterable[TranscriptSegment],
    max_items: int = 12,
    min_gap_seconds: int = 90,
) -> list[TranscriptSegment]:
    chosen: list[TranscriptSegment] = []
    last = -10_000.0
    for segment in segments:
        if not chosen or segment.start - last >= min_gap_seconds:
            chosen.append(segment)
            last = segment.start
        if len(chosen) >= max_items:
            break
    return chosen


def build_markdown(video: VideoData, summary: str) -> str:
    safe_title = escape(video.title, quote=False)
    lines = [
        f"# {safe_title}",
        "",
        f"[{safe_title}]({video.canonical_url})",
        f"Channel: {video.channel}",
        f"Published: {video.published}",
        "",
        "## Summary",
        summary.strip(),
        "",
        "## Notable timestamps",
    ]

    for segment in pick_notable_timestamps(video.transcript):
        timestamp = format_timestamp(segment.start)
        url = _timestamp_url(video.canonical_url, segment.start)
        topic = _topic_from_text(segment.text)
        lines.append(f"- [{timestamp}]({url}) — {topic}")

    if lines[-1] == "## Notable timestamps":
        lines.append("- No timestamped transcript segments found.")

    lines.append("")
    return "\n".join(lines)
