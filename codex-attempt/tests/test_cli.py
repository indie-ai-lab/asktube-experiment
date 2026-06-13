from pathlib import Path

import cli
from youtube import TranscriptSegment, Video


VIDEO = Video(
    video_id="jNQXAC9IVRw",
    title="Me at the zoo",
    channel="jawed",
    published="Unknown",
    canonical_url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
    transcript=(TranscriptSegment("All right, so here we are", 0, 5),),
)


def test_cli_writes_default_output(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    monkeypatch.setattr(cli, "fetch_video", lambda _url: VIDEO)
    monkeypatch.setattr(cli, "summarize", lambda *_args, **_kwargs: "- A summary")

    assert cli.main(["https://youtu.be/jNQXAC9IVRw"]) == 0

    output = Path("jNQXAC9IVRw.md").read_text()
    assert "# Me at the zoo" in output
    assert "- A summary" in output


def test_cli_uses_selected_provider_key(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.setattr(cli, "fetch_video", lambda _url: VIDEO)
    received = {}

    def fake_summarize(_transcript, **kwargs):
        received.update(kwargs)
        return "- A summary"

    monkeypatch.setattr(cli, "summarize", fake_summarize)

    output = tmp_path / "result.md"
    assert (
        cli.main(
            ["https://youtu.be/jNQXAC9IVRw", "--model", "gpt", "--out", str(output)]
        )
        == 0
    )
    assert received["provider"] == "gpt"
    assert received["api_key"] == "openai-secret"


def test_cli_fails_cleanly_when_api_key_is_missing(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert cli.main(["https://youtu.be/jNQXAC9IVRw"]) == 1
    assert "ANTHROPIC_API_KEY is not set" in capsys.readouterr().err


def test_cli_fails_cleanly_for_invalid_url(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert cli.main(["not-a-url"]) == 1
    assert "valid YouTube URL" in capsys.readouterr().err
