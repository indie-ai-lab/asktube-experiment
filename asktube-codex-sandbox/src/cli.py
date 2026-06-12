"""Command-line entry point for AskTube."""

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

from formatter import format_markdown
from summarizer import LLMError, summarize
from youtube import YouTubeError, fetch_video, parse_video_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize a YouTube transcript as Markdown."
    )
    parser.add_argument("youtube_url", help="YouTube video URL")
    parser.add_argument(
        "--out", type=Path, help="Output path (default: ./<video_id>.md)"
    )
    parser.add_argument("--model", choices=("claude", "gpt"), default="claude")
    parser.add_argument(
        "--length", choices=("short", "medium", "long"), default="medium"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        video_id = parse_video_id(args.youtube_url)
    except YouTubeError as exc:
        print(f"asktube: error: {exc}", file=sys.stderr)
        return 1

    env_name = "ANTHROPIC_API_KEY" if args.model == "claude" else "OPENAI_API_KEY"
    api_key = os.getenv(env_name)
    if not api_key:
        print(f"asktube: error: {env_name} is not set.", file=sys.stderr)
        return 1

    try:
        output_path = args.out or Path(f"{video_id}.md")
        video = fetch_video(args.youtube_url)
        summary = summarize(
            video.transcript, provider=args.model, length=args.length, api_key=api_key
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(format_markdown(video, summary), encoding="utf-8")
    except (YouTubeError, LLMError, OSError) as exc:
        print(f"asktube: error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
