from youtube import TranscriptSegment, VideoData
from formatter import build_markdown, format_timestamp, pick_notable_timestamps


def test_format_timestamp():
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(134) == "02:14"
    assert format_timestamp(3723) == "01:02:03"


def test_build_markdown_contains_required_sections():
    video = VideoData(
        video_id="jNQXAC9IVRw",
        title="Me at the zoo",
        channel="jawed",
        published="Unknown",
        canonical_url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
        transcript=[TranscriptSegment(0, 2, "The first topic")],
    )

    md = build_markdown(video, "- A short summary")

    assert "# Me at the zoo" in md
    assert "[Me at the zoo](https://www.youtube.com/watch?v=jNQXAC9IVRw)" in md
    assert "Channel: jawed" in md
    assert "Published: Unknown" in md
    assert "## Summary" in md
    assert "## Notable timestamps" in md
    assert "[00:00](https://www.youtube.com/watch?v=jNQXAC9IVRw&t=0s)" in md


def test_pick_notable_timestamps_respects_gap():
    segments = [
        TranscriptSegment(0, 1, "a"),
        TranscriptSegment(20, 1, "b"),
        TranscriptSegment(95, 1, "c"),
    ]
    chosen = pick_notable_timestamps(segments, min_gap_seconds=90)
    assert [s.text for s in chosen] == ["a", "c"]
