import sys
from types import SimpleNamespace

import pytest

from summarizer import LLMError, summarize
from youtube import TranscriptSegment


TRANSCRIPT = (TranscriptSegment("Hello from the video", 0, 1),)


def test_summarize_calls_anthropic(monkeypatch):
    calls = {}

    class Messages:
        def create(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(text="- Claude summary")])

    class Anthropic:
        def __init__(self, api_key):
            assert api_key == "secret"
            self.messages = Messages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=Anthropic))

    result = summarize(TRANSCRIPT, provider="claude", length="short", api_key="secret")

    assert result == "- Claude summary"
    assert calls["model"] == "claude-haiku-4-5"
    assert "about 5 concise bullets" in calls["messages"][0]["content"]


def test_summarize_calls_openai(monkeypatch):
    calls = {}

    class Completions:
        def create(self, **kwargs):
            calls.update(kwargs)
            message = SimpleNamespace(content="- GPT summary")
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class OpenAI:
        def __init__(self, api_key):
            assert api_key == "secret"
            self.chat = SimpleNamespace(completions=Completions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=OpenAI))

    result = summarize(TRANSCRIPT, provider="gpt", length="long", api_key="secret")

    assert result == "- GPT summary"
    assert calls["model"].startswith("gpt-")
    assert "roughly 500 words" in calls["messages"][0]["content"]


def test_summarize_wraps_provider_failures(monkeypatch):
    class Messages:
        def create(self, **_kwargs):
            raise RuntimeError("rate limit exceeded")

    class Anthropic:
        def __init__(self, **_kwargs):
            self.messages = Messages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=Anthropic))

    with pytest.raises(LLMError, match="rate limit exceeded"):
        summarize(TRANSCRIPT, provider="claude", length="medium", api_key="secret")
