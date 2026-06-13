# Observations — ChatGPT vs Codex on AskTube

Same prompt (the README at the root of this repo) handed to two
OpenAI tools. Final recorded run for each was zero human interventions —
both shipped a working result from a single prompt.

## Numbers

| Axis | ChatGPT (GPT-5) | Codex (codex-1) |
|---|---|---|
| Total elapsed wall time | **4.7 min** | **8.0 min** |
| Human active time | ~most of it (chat back-and-forth) | ~zero (handed off, watched) |
| Human interventions | 0 | 0 |
| Tests written | 16 | 14 |
| Tests passing | 16 / 16 | 14 / 14 (Python 3.10+) |
| LOC — total | 678 | 530 |
| LOC — src/ only | 479 | 306 |
| LOC — tests/ only | 199 | 224 |
| Python compatibility | 3.9+ (`from __future__`) | strict 3.10+ (PEP 604) |
| Mark (final) | ◎ | ◎ |

Both shipped working software. The interesting thing is *how* they got
there, not *whether*.

## What was different

### 1. Codex's `src/` is ~36% smaller

Same external behavior, ~170 fewer lines in `src/`. The biggest gap is
in `summarizer.py`:

- ChatGPT: 162 lines — more error classes, more retry wrappers,
  separate "build prompt", "call Anthropic", "call OpenAI" functions
- Codex: 71 lines — single `summarize(...)` function that dispatches
  by provider; one error class

Both pass tests. ChatGPT is more defensive; Codex is more direct. Which
you prefer is taste — but the 2× LOC difference is real and
reproducible from the same prompt.

### 2. Different stance on Python version

- ChatGPT: `from __future__ import annotations` at the top of every
  file → annotations are strings → 3.9 keeps working
- Codex: `Sequence[str] | None` PEP-604 union syntax → strict 3.10+

The spec says "Python 3.10+", so Codex is technically more "correct"
per the spec. ChatGPT is more conservative, presumably hedging against
older runtimes. Two valid readings of "3.10+".

### 3. Time spent vs time present

The recordings differ by 3.3 min, but the *human* time is the opposite:

- **ChatGPT (4.7 min, mostly active)**: chatting back-and-forth, copying
  code into local files as it streams.
- **Codex (8.0 min, mostly passive)**: one prompt in, then the agent
  did the rest. Human watched the progress bar.

If "time present at the keyboard" is what matters, Codex wins. If
"time elapsed before I have something" is what matters, ChatGPT wins.

### 4. They picked the same architecture

Same four files in `src/`. Same four files in `tests/`. Same separation
of concerns (URL parsing → metadata + transcript → LLM call →
Markdown formatting). Neither one invented a different layout.

That convergence is interesting on its own — two different "minds"
arrived at the same skeleton from the same one-paragraph prompt.

### 5. Subtle library-usage tells

- ChatGPT calls `YouTubeTranscriptApi.get_transcript(id)` as a class
  method (the older API style of the library).
- Codex instantiates: `api = YouTubeTranscriptApi(); api.fetch(id)`
  (newer instance-based API).

Same library, different recent-vs-older mental models. Possibly a
training-cutoff artifact, possibly a stylistic preference. Either way,
you can spot which AI wrote which without reading the README.

## What surprised me

- **Codex stopping to ask clarifying questions early on.** First run
  asked "build at root or in `codex-attempt/`?" and a second small
  question. I added a "don't ask, just ship, document defaults"
  section to the README, and the rerun went 0-interventions. This is
  a real difference from ChatGPT's chat: agentic tools default to
  *checking*, chat defaults to *guessing*. The "right" behavior is
  spec-dependent.
- **Both wrote tests that mock the LLM call.** Neither hardcoded API
  responses or skipped the LLM tests. That's actually a higher quality
  bar than I expected from a one-shot prompt.
- **Neither one used the optional stretch goals.** Both took "skip
  unless trivial" seriously and shipped just the core. Codex was
  slightly more disciplined about this (cleaner README, no extra
  features); ChatGPT included a bit more error-class scaffolding that
  isn't strictly required.

## What I'd give each tool next time

- **ChatGPT**: a longer/more ambiguous spec. It excels at "shape the
  thing while we talk" — which we didn't do here. The chat format is
  wasted on a fully-specified prompt.
- **Codex**: a *bigger* task than this one. The 8-min walk-away win
  scales linearly with task size — a 30-min task pays back the
  hand-off overhead much more than a 5-min one does.

## The verdict (not a recommendation)

> **They're different in a way that changes what your day looks like,
> not just what your screen looks like.**

If your day is 1-hour bursts at the keyboard, ChatGPT keeps you in
flow. If your day is "queue five things, walk away, come back to PRs",
Codex is the loop.

Neither one "won" AskTube. Both shipped. The choice is about your
workflow shape, not their capability gap.
