# AskTube

AskTube turns a YouTube video's captions into a Markdown summary with clickable
timestamp anchors.

## Install

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Set the API key for the provider you plan to use:

```bash
export ANTHROPIC_API_KEY="..."
# or
export OPENAI_API_KEY="..."
```

## Use

```bash
asktube https://www.youtube.com/watch?v=jNQXAC9IVRw
asktube https://youtu.be/jNQXAC9IVRw --model gpt --length short --out summary.md
```

The default provider is `claude`, the default length is `medium`, and the
default output path is `./<video_id>.md`. Set `ANTHROPIC_MODEL` or
`OPENAI_MODEL` to override the provider's default model.

AskTube fetches captions with `youtube-transcript-api`. It uses YouTube's free
oEmbed endpoint for title and channel metadata; publish date is emitted as
`Unknown` because oEmbed does not provide it.

## Test

```bash
pip install -e ".[test]"
pytest
```
