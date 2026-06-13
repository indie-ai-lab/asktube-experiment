from __future__ import annotations

import sys
import types

import pytest

from summarizer import MissingAPIKeyError, summarize_transcript
from youtube import TranscriptSegment


def test_missing_claude_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError):
        summarize_transcript([TranscriptSegment(0, 1, "hi")], title="t", provider="claude")


def test_summarize_with_openai_response_api(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    module = types.ModuleType("openai")

    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["model"] == "gpt-4o-mini"
            assert "Transcript:" in kwargs["input"]
            return types.SimpleNamespace(output_text="- summary")

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.responses = FakeResponses()

    module.OpenAI = FakeClient
    module.RateLimitError = type("RateLimitError", (Exception,), {})
    monkeypatch.setitem(sys.modules, "openai", module)

    result = summarize_transcript(
        [TranscriptSegment(0, 1, "hello")], title="Title", provider="gpt", length="short"
    )
    assert result == "- summary"


def test_summarize_with_claude(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    module = types.ModuleType("anthropic")

    class FakeMessages:
        def create(self, **kwargs):
            assert kwargs["model"] == "claude-3-5-sonnet-latest"
            assert kwargs["messages"][0]["role"] == "user"
            return types.SimpleNamespace(content=[types.SimpleNamespace(text="- claude summary")])

    class FakeAnthropic:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.messages = FakeMessages()

    module.Anthropic = FakeAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", module)

    result = summarize_transcript(
        [TranscriptSegment(0, 1, "hello")], title="Title", provider="claude", length="medium"
    )
    assert result == "- claude summary"
