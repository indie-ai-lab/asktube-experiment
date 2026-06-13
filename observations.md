# Observations — ChatGPT vs Codex on AskTube

Same prompt (the README at the root of this repo) handed to two
OpenAI tools. Final recorded run for each was zero human interventions —
both shipped a working result from a single prompt.

## Numbers

| Axis | ChatGPT (GPT-5) | Codex (codex-1) |
|---|---|---|
| Recording duration | 4.7 min | 8.0 min |
| **Estimated AI work time** (prompt → final artifact) | **~1.5 min** | **~7 min** |
| Source for the estimate | file mtimes in zip (`18:12–18:13`) vs recording start `18:11:07` | git commit time `18:59:07` vs recording start `18:52:01` |
| Human interventions | 0 | 0 |
| Tests written | 16 | 14 |
| Tests passing | 16 / 16 | 14 / 14 (Python 3.10+) |
| Tests verified by the AI itself | No | Yes (Codex ran them green before handing over) |
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

### 3. Same "working code" — different verification level at hand-off

Both ran 0-intervention once the spec was clear; the human walked away
in both cases. So the popular "ChatGPT keeps you at the keyboard"
framing doesn't hold for a well-specced task — neither does.

The real difference is what each tool does *before* it hands the code
back:

- **ChatGPT** writes the code and the tests and hands them over.
  It does not run the tests itself.
- **Codex** writes the code and the tests, **runs the tests, fixes
  failures, and hands over only after they go green**.

Codex's extra ~5 minutes (~7 min total vs ~1.5 for ChatGPT) is spent
inside the verify-and-iterate loop.

The result:

- **ChatGPT's code is "probably works"** — whoever receives it runs
  pytest for the first time.
- **Codex's code is "tests are green on my machine"** — already verified
  by the AI before delivery.

In our run, both happened to ship working code. But that's GPT-5 being
good enough to land it without verification — not a guarantee. On edge-
case-heavier real tasks, the verification gap shows up as actual bugs.

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

If you need a result *now* and you're comfortable trusting "probably
works" code, ChatGPT delivers in ~1–2 minutes. If you'd rather come
back to *verified* code and don't mind waiting ~7 minutes, Codex
hands you a tested artifact.

Neither one "won" AskTube. Both shipped. The choice is about whether
you value speed-to-first-draft or verification-before-hand-off — and
how big the task is. Bigger tasks tilt the trade toward Codex; tiny
quick-question-style tasks tilt back toward ChatGPT.
