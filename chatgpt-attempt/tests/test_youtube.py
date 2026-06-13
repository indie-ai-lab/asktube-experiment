from __future__ import annotations

import sys
import types

import pytest

from youtube import (
    TranscriptSegment,
    fetch_transcript,
    parse_video_id,
    InvalidYouTubeURLError,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "https://www.youtube.com/watch?v=jNQXAC9IVRw&t=10s",
        "https://youtu.be/jNQXAC9IVRw?si=abc",
        "youtube.com/embed/jNQXAC9IVRw",
        "https://www.youtube.com/shorts/jNQXAC9IVRw",
        "jNQXAC9IVRw",
    ],
)
def test_parse_video_id_valid(url):
    assert parse_video_id(url) == "jNQXAC9IVRw"


def test_parse_video_id_invalid():
    with pytest.raises(InvalidYouTubeURLError):
        parse_video_id("https://example.com/watch?v=jNQXAC9IVRw")


def test_fetch_transcript_normalizes_segments(monkeypatch):
    module = types.ModuleType("youtube_transcript_api")

    class FakeAPI:
        def fetch(self, video_id, languages):
            assert video_id == "jNQXAC9IVRw"
            assert languages == ["en"]
            return [
                {"start": 0, "duration": 1.5, "text": "Hello\nthere"},
                types.SimpleNamespace(start=2, duration=1, text=" General Kenobi "),
            ]

    module.YouTubeTranscriptApi = FakeAPI
    monkeypatch.setitem(sys.modules, "youtube_transcript_api", module)

    assert fetch_transcript("jNQXAC9IVRw") == [
        TranscriptSegment(start=0.0, duration=1.5, text="Hello there"),
        TranscriptSegment(start=2.0, duration=1.0, text="General Kenobi"),
    ]
