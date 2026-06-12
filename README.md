# AskTube — the same coding task, two OpenAI tools

This repo is the spec + receipts for an Indie AI Lab experiment:

> **The same coding task, given to ChatGPT (chat) and Codex (agent).
> Both come from OpenAI. We watched what each one produced.**

The video lives at [Indie AI Lab on YouTube](https://www.youtube.com/@IndieAILaboratory).
This repo is the artifact — anyone can reproduce the experiment from
the spec below, or read what each tool actually shipped.

---

## The task — AskTube

Build a small CLI tool that:

1. Takes a YouTube video URL
2. Fetches the video's transcript
3. Sends the transcript to an LLM for summarization
4. Saves the summary as a Markdown file with timestamp anchors

### Interface

```
asktube <youtube_url> [--out PATH] [--model claude|gpt] [--length short|medium|long]
```

- `<youtube_url>` — required. Any standard YouTube URL form (`youtube.com/watch?v=...`,
  `youtu.be/...`, with or without query params).
- `--out PATH` — optional. Defaults to `./<video_id>.md`.
- `--model {claude,gpt}` — optional. Defaults to `claude`. Uses
  `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` from env accordingly.
- `--length {short,medium,long}` — optional. Defaults to `medium`.
  Controls the summary's target length (roughly: short = 5 bullets,
  medium = 10–15 bullets, long = section-structured ~500 words).

### Expected file structure

```
src/
├── cli.py            # entry point, argparse, orchestration
├── youtube.py        # fetch transcript (use youtube-transcript-api or similar)
├── summarizer.py     # call Anthropic / OpenAI SDK, return summary text
└── formatter.py      # build the final Markdown output
tests/
├── test_cli.py
├── test_youtube.py   # mock the transcript fetch
├── test_summarizer.py # mock the LLM call
└── test_formatter.py
pyproject.toml
README.md
```

### Output format

The generated Markdown should include, at minimum:

```markdown
# <video title>

[<video title>](<canonical youtube url>)
Channel: <channel name>
Published: <YYYY-MM-DD>

## Summary
<bullet list or sections per the --length flag>

## Notable timestamps
- [00:00](<url>&t=0s) — <topic>
- [02:14](<url>&t=134s) — <topic>
- ...
```

### Acceptance criteria

- `pip install -e .` works in a fresh venv
- `asktube https://www.youtube.com/watch?v=jNQXAC9IVRw` produces a
  sensible Markdown file (this is a real test video — 19 seconds long,
  has captions)
- `pytest` exits 0 with no failures
- No hardcoded API keys; reads from environment only
- Errors gracefully on: invalid URL, video without transcript,
  LLM rate limit

### Constraints

- Python 3.10+
- Anthropic SDK ≥ 0.40 or OpenAI SDK ≥ 1.50
- Use `youtube-transcript-api` (or equivalent) for transcript fetch —
  no scraping
- Keep total LOC under ~500 lines; this is a focused tool, not a framework

### Build instructions (please follow)

This spec is being given to **multiple AI tools at once** for a
comparison experiment. To make the runs comparable, please:

- **Ship a working result, don't ask clarifying questions.** If the
  spec is ambiguous on a detail, pick a sensible default, leave a brief
  `# NOTE:` comment explaining the choice, and keep building.
- **Build at the repository root** (don't place files under any
  subdirectory like `chatgpt-attempt/` or `codex-attempt/` — those are
  archive folders the human will populate after).
- **No extra API keys**. If a piece of metadata (video title, channel,
  publish date) isn't reachable via `youtube-transcript-api` or a free
  public endpoint, just emit `Unknown` for that field. Do not require
  the user to set up a YouTube Data API key.
- **Skip optional stretch goals** unless you have spare time after the
  acceptance criteria pass. Stretch goals are for "if it's easy", not
  for blocking the main deliverable.
- One final commit/PR is preferred over many WIP commits.

### Stretch goals (optional)

- Stream the LLM response (don't buffer entire summary)
- Detect transcript language and prompt the LLM to respond in the
  same language
- Cache results by `<video_id>` in `~/.cache/asktube/` to avoid re-billing

---

## What's in this repo

```
asktube-experiment/
├── README.md           ← you are here (the spec)
├── chatgpt-attempt/    ← what ChatGPT (GPT-5) produced when given the
│                          spec above as a single prompt
├── codex-attempt/      ← what Codex (codex-1) produced when given the
│                          same spec via the Codex agent on a fresh repo
└── observations.md     ← human notes: wall-time, interventions, costs,
                          surprises, final verdict
```

Both attempts are committed as-is, including any bugs or odd choices.
The point is to compare what shipped, not to clean up after either AI.

## Reproducing the experiment

1. Clone this repo
2. Open the spec in `README.md`
3. Hand it to ChatGPT in a single new chat — no follow-up clarifications
4. Hand it to Codex with the same spec on a fresh empty repo
5. Time each session, log interventions, ship the result

The Indie AI Lab video walks through what happened step by step.
