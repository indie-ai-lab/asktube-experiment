from __future__ import annotations

from argparse import Namespace

import cli
from youtube import TranscriptSegment, VideoData


def test_run_writes_markdown(monkeypatch, tmp_path):
    video = VideoData(
        video_id="jNQXAC9IVRw",
        title="Me at the zoo",
        channel="jawed",
        published="Unknown",
        canonical_url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
        transcript=[TranscriptSegment(0, 2, "Hello")],
    )

    monkeypatch.setattr(cli, "fetch_video", lambda url: video)
    monkeypatch.setattr(cli, "summarize_transcript", lambda *args, **kwargs: "- summary")

    out = tmp_path / "out.md"
    result = cli.run(
        Namespace(
            youtube_url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
            out=str(out),
            model="claude",
            length="medium",
        )
    )

    assert result == out
    assert "# Me at the zoo" in out.read_text(encoding="utf-8")


def test_main_returns_error_on_invalid_url(capsys):
    exit_code = cli.main(["not-a-youtube-url"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid URL" in captured.err
