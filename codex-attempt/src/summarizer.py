"""LLM-backed transcript summarization."""

import os
from typing import Iterable

from youtube import TranscriptSegment


class LLMError(Exception):
    """Raised when an LLM provider cannot produce a summary."""


LENGTH_INSTRUCTIONS = {
    "short": "Write about 5 concise bullets.",
    "medium": "Write 10-15 concise bullets.",
    "long": "Write a section-structured summary of roughly 500 words.",
}


def _build_prompt(transcript: Iterable[TranscriptSegment], length: str) -> str:
    lines = "\n".join(
        f"[{int(item.start // 60):02d}:{int(item.start % 60):02d}] {item.text}"
        for item in transcript
    )
    return (
        "Summarize this YouTube transcript in Markdown. "
        f"{LENGTH_INSTRUCTIONS[length]} Focus on concrete ideas and omit preamble.\n\n"
        f"Transcript:\n{lines}"
    )


def summarize(
    transcript: Iterable[TranscriptSegment],
    *,
    provider: str,
    length: str,
    api_key: str,
) -> str:
    """Return a Markdown summary using the selected provider."""
    prompt = _build_prompt(transcript, length)
    try:
        if provider == "claude":
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
                max_tokens={"short": 500, "medium": 1000, "long": 1800}[length],
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
        elif provider == "gpt":
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens={"short": 500, "medium": 1000, "long": 1800}[length],
            )
            text = response.choices[0].message.content
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as exc:
        raise LLMError(f"{provider} request failed: {exc}") from exc

    if not text or not text.strip():
        raise LLMError(f"{provider} returned an empty summary.")
    return text.strip()
