import pytest

from youtube import (
    InvalidYouTubeURL,
    TranscriptUnavailable,
    fetch_video,
    parse_video_id,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=jNQXAC9IVRw", "jNQXAC9IVRw"),
        ("https://youtu.be/jNQXAC9IVRw?t=4", "jNQXAC9IVRw"),
        ("https://youtube.com/shorts/jNQXAC9IVRw?feature=share", "jNQXAC9IVRw"),
    ],
)
def test_parse_video_id_accepts_standard_urls(url, expected):
    assert parse_video_id(url) == expected


def test_parse_video_id_rejects_invalid_url():
    with pytest.raises(InvalidYouTubeURL, match="valid YouTube URL"):
        parse_video_id("https://example.com/watch?v=jNQXAC9IVRw")


def test_fetch_video_normalizes_transcript_and_metadata():
    class Segment:
        text = "Hello world"
        start = 0.0
        duration = 2.5

    class TranscriptApi:
        def fetch(self, video_id):
            assert video_id == "jNQXAC9IVRw"
            return [Segment()]

    video = fetch_video(
        "https://youtu.be/jNQXAC9IVRw",
        transcript_api=TranscriptApi(),
        metadata_fetcher=lambda _url: {
            "title": "Me at the zoo",
            "author_name": "jawed",
        },
    )

    assert video.video_id == "jNQXAC9IVRw"
    assert video.title == "Me at the zoo"
    assert video.channel == "jawed"
    assert video.published == "Unknown"
    assert video.transcript[0].text == "Hello world"


def test_fetch_video_reports_missing_transcript():
    class TranscriptApi:
        def fetch(self, _video_id):
            raise RuntimeError("captions disabled")

    with pytest.raises(TranscriptUnavailable, match="Transcript unavailable"):
        fetch_video(
            "https://youtu.be/jNQXAC9IVRw",
            transcript_api=TranscriptApi(),
            metadata_fetcher=lambda _url: {},
        )
