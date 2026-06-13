# AskTube

AskTube is a small CLI tool that fetches a YouTube transcript, asks an LLM to summarize it, and saves a timestamped Markdown file.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configure

For Claude, set:

```bash
export ANTHROPIC_API_KEY="..."
```

For GPT, set:

```bash
export OPENAI_API_KEY="..."
```

Optional model overrides:

```bash
export ANTHROPIC_MODEL="claude-3-5-sonnet-latest"
export OPENAI_MODEL="gpt-4o-mini"
```

## Usage

```bash
asktube <youtube_url> [--out PATH] [--model claude|gpt] [--length short|medium|long]
```

Examples:

```bash
asktube https://www.youtube.com/watch?v=jNQXAC9IVRw
asktube https://youtu.be/jNQXAC9IVRw --model gpt --length short --out zoo.md
```

`--out` defaults to `./<video_id>.md`.

## Output

The Markdown output contains:

- video title and canonical URL
- channel name
- published date field, set to `Unknown` by default because YouTube oEmbed does not expose publish dates
- LLM-generated summary
- timestamp links derived from transcript segments

## Tests

```bash
pip install -e .[dev]
pytest
```

## Notes

- Transcript fetching uses `youtube-transcript-api`; no transcript scraping is used.
- Title/channel metadata uses YouTube oEmbed.
- API keys are read only from environment variables.
- User-facing errors are returned for invalid URLs, missing transcripts, missing API keys, and LLM rate limits.
