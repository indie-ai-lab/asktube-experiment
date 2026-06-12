"""Markdown output formatting."""

from youtube import TranscriptSegment, Video


def _timestamp(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return (
        f"{hours:02d}:{minutes:02d}:{secs:02d}"
        if hours
        else f"{minutes:02d}:{secs:02d}"
    )


def _notable_segments(
    transcript: tuple[TranscriptSegment, ...],
) -> tuple[TranscriptSegment, ...]:
    if len(transcript) <= 6:
        return transcript
    indexes = sorted({round(index * (len(transcript) - 1) / 5) for index in range(6)})
    return tuple(transcript[index] for index in indexes)


def _topic(text: str) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= 90 else f"{compact[:87]}..."


def format_markdown(video: Video, summary: str) -> str:
    """Build the final Markdown document."""
    timestamps = "\n".join(
        f"- [{_timestamp(segment.start)}]({video.canonical_url}&t={int(segment.start)}s) — {_topic(segment.text)}"
        for segment in _notable_segments(video.transcript)
    )
    return (
        f"# {video.title}\n\n"
        f"[{video.title}]({video.canonical_url})\n"
        f"Channel: {video.channel}\n"
        f"Published: {video.published}\n\n"
        f"## Summary\n{summary.strip()}\n\n"
        f"## Notable timestamps\n{timestamps}\n"
    )
