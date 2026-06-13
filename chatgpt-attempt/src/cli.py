"""Command-line entry point for AskTube."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from formatter import build_markdown
from summarizer import LLMRateLimitError, MissingAPIKeyError, SummarizerError, summarize_transcript
from youtube import InvalidYouTubeURLError, TranscriptUnavailableError, fetch_video, parse_video_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asktube",
        description="Summarize a YouTube transcript to a timestamped Markdown file.",
    )
    parser.add_argument("youtube_url", help="Any standard YouTube video URL")
    parser.add_argument("--out", help="Output Markdown path. Defaults to ./<video_id>.md")
    parser.add_argument("--model", choices=("claude", "gpt"), default="claude")
    parser.add_argument("--length", choices=("short", "medium", "long"), default="medium")
    return parser


def _default_out(url: str) -> Path:
    return Path(f"{parse_video_id(url)}.md")


def run(args: argparse.Namespace) -> Path:
    out_path = Path(args.out) if args.out else _default_out(args.youtube_url)
    video = fetch_video(args.youtube_url)
    summary = summarize_transcript(
        video.transcript,
        title=video.title,
        provider=args.model,
        length=args.length,
    )
    markdown = build_markdown(video, summary)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    return out_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        out_path = run(args)
    except InvalidYouTubeURLError as exc:
        print(f"asktube: invalid URL: {exc}", file=sys.stderr)
        return 2
    except TranscriptUnavailableError as exc:
        print(f"asktube: transcript unavailable: {exc}", file=sys.stderr)
        return 3
    except LLMRateLimitError as exc:
        print(f"asktube: LLM rate limit: {exc}", file=sys.stderr)
        return 4
    except MissingAPIKeyError as exc:
        print(f"asktube: configuration error: {exc}", file=sys.stderr)
        return 5
    except SummarizerError as exc:
        print(f"asktube: summarization failed: {exc}", file=sys.stderr)
        return 6

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
