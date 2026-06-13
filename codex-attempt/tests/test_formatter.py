from formatter import format_markdown
from youtube import TranscriptSegment, Video


def test_format_markdown_includes_metadata_summary_and_timestamp_links():
    video = Video(
        video_id="abc123XYZ_-",
        title="A useful video",
        channel="A channel",
        published="Unknown",
        canonical_url="https://www.youtube.com/watch?v=abc123XYZ_-",
        transcript=(
            TranscriptSegment("Opening idea", 0, 4),
            TranscriptSegment("A later topic", 134, 5),
        ),
    )

    output = format_markdown(video, "- First insight\n- Second insight")

    assert output.startswith("# A useful video\n")
    assert "[A useful video](https://www.youtube.com/watch?v=abc123XYZ_-)" in output
    assert "Channel: A channel\nPublished: Unknown" in output
    assert "## Summary\n- First insight" in output
    assert (
        "- [02:14](https://www.youtube.com/watch?v=abc123XYZ_-&t=134s) — A later topic"
    ) in output
