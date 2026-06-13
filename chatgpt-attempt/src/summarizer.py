"""LLM summarization clients for Anthropic and OpenAI."""

from __future__ import annotations

import os
from typing import Literal, Sequence

from formatter import format_timestamp
from youtube import TranscriptSegment

SummaryLength = Literal["short", "medium", "long"]
ModelProvider = Literal["claude", "gpt"]


class SummarizerError(Exception):
    """Base exception for summarization failures."""


class MissingAPIKeyError(SummarizerError):
    """Raised when the needed API key is missing."""


class LLMRateLimitError(SummarizerError):
    """Raised when the provider reports a rate limit."""


_LENGTH_INSTRUCTIONS = {
    "short": "Return about 5 concise bullets.",
    "medium": "Return 10 to 15 concise bullets.",
    "long": "Return section-structured notes of roughly 500 words.",
}


def _transcript_text(segments: Sequence[TranscriptSegment], max_chars: int = 80_000) -> str:
    lines = [f"[{format_timestamp(s.start)}] {s.text}" for s in segments]
    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0] + "\n[Transcript truncated]"


def _prompt(title: str, segments: Sequence[TranscriptSegment], length: SummaryLength) -> str:
    return f"""Summarize this YouTube transcript in Markdown.

Video title: {title}
Target length: {_LENGTH_INSTRUCTIONS[length]}

Rules:
- Prefer useful, specific takeaways over generic commentary.
- Keep the summary faithful to the transcript.
- Do not invent facts that are not in the transcript.
- Include timestamps inline only when they help the reader.

Transcript:
{_transcript_text(segments)}
"""


def summarize_transcript(
    segments: Sequence[TranscriptSegment],
    *,
    title: str,
    provider: ModelProvider = "claude",
    length: SummaryLength = "medium",
) -> str:
    if provider == "claude":
        return _summarize_with_claude(title, segments, length)
    if provider == "gpt":
        return _summarize_with_openai(title, segments, length)
    raise ValueError(f"Unsupported model provider: {provider}")


def _summarize_with_claude(
    title: str,
    segments: Sequence[TranscriptSegment],
    length: SummaryLength,
) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise MissingAPIKeyError("ANTHROPIC_API_KEY is not set.")

    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - installation issue
        raise SummarizerError("anthropic is not installed. Run: pip install -e .") from exc

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            max_tokens={"short": 400, "medium": 900, "long": 1400}[length],
            temperature=0.2,
            messages=[{"role": "user", "content": _prompt(title, segments, length)}],
        )
    except Exception as exc:  # noqa: BLE001 - normalize SDK-specific errors
        if exc.__class__.__name__.lower().startswith("ratelimit"):
            raise LLMRateLimitError("Anthropic rate limit reached. Try again later.") from exc
        raise SummarizerError(f"Anthropic summarization failed: {exc}") from exc

    parts: list[str] = []
    for block in getattr(message, "content", []):
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(str(text))
    result = "\n".join(parts).strip()
    if not result:
        raise SummarizerError("Anthropic returned an empty summary.")
    return result


def _summarize_with_openai(
    title: str,
    segments: Sequence[TranscriptSegment],
    length: SummaryLength,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingAPIKeyError("OPENAI_API_KEY is not set.")

    try:
        import openai
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - installation issue
        raise SummarizerError("openai is not installed. Run: pip install -e .") from exc

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        client = OpenAI(api_key=api_key)
        if hasattr(client, "responses"):
            response = client.responses.create(
                model=model,
                instructions="You produce faithful Markdown summaries of video transcripts.",
                input=_prompt(title, segments, length),
                temperature=0.2,
                max_output_tokens={"short": 400, "medium": 900, "long": 1400}[length],
            )
            result = getattr(response, "output_text", "").strip()
        else:  # pragma: no cover - compatibility for older SDKs
            completion = client.chat.completions.create(
                model=model,
                temperature=0.2,
                max_tokens={"short": 400, "medium": 900, "long": 1400}[length],
                messages=[
                    {
                        "role": "system",
                        "content": "You produce faithful Markdown summaries of video transcripts.",
                    },
                    {"role": "user", "content": _prompt(title, segments, length)},
                ],
            )
            result = completion.choices[0].message.content.strip()
    except Exception as exc:  # noqa: BLE001 - normalize SDK-specific errors
        rate_limit_error = getattr(openai, "RateLimitError", None)
        if (rate_limit_error and isinstance(exc, rate_limit_error)) or exc.__class__.__name__ == "RateLimitError":
            raise LLMRateLimitError("OpenAI rate limit reached. Try again later.") from exc
        raise SummarizerError(f"OpenAI summarization failed: {exc}") from exc

    if not result:
        raise SummarizerError("OpenAI returned an empty summary.")
    return result
