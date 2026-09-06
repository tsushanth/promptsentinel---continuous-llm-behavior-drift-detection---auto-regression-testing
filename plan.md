# PromptSentinel — Local MVP Scaffold Plan

Goal: prove the core loop — **capture real prompt/output pairs → pin a baseline →
re-run the same prompts later (or against a different model) → diff outputs →
flag drift (structure, refusal, tone, JSON-parseability) → show which prompts
regressed** — running entirely on one machine, with no server, accounts, or
deployment.

## 1. Stack choice

**Python 3 stdlib-first CLI, single package, zero required third-party deps
to run the offline demo.**

- `argparse`-based CLI (no Click/Typer/FastAPI/DB) — one process, one command
  at a time, nothing to keep running.
- Data persisted as flat JSONL/JSON files on disk (no SQLite/Postgres) — a
  drift tool's core artifact is "here are the two outputs and the diff," which
  a JSON blob represents perfectly and is trivially inspectable with `cat`.
- Real provider calls (OpenAI/Anthropic/Gemini SDKs) are **optional, isolated
  behind a `Provider` interface**, and only exercised if the user has already
  exported their own API key as an env var (BYO key — not a PromptSentinel
  account). The default, no-key path uses a **mock provider** seeded with
  canned "before" and "after" (drifted) responses so the entire flow —
  capture, baseline, drift run, diff report — works fully offline, free, and
  deterministically. This is what makes the demo "near-instant and nearly
  free" per the pitch, and it's how we sidestep needing live API billing to
  prove the concept.
- Diffing uses stdlib only: `difflib` for text similarity, `json.loads` for
  parseability checks, and small keyword/regex heuristics for refusal
  detection ("I cannot", "I'm sorry, but", etc.) and gross tone shift (e.g.
  response length delta, apology-phrase count). This is intentionally crude —
  good enough to demonstrate "we caught a regression," not a production NLP
  classifier.

Why not Node/TS or Go: the diffing logic is string/JSON heuristics and file
I/O — Python's stdlib (`difflib`, `json`) is the least code for that. No
compiled binary or npm ecosystem is needed to prove the idea.

## 2. Explicitly out of scope for this local MVP

- No auth, accounts, or multi-user concept of any kind.
- No billing/metering.
- No hosting, deployment, or "proxy server" listening on a network port —
  the "proxy" is simulated as a thin Python wrapper function you import and
  call in-process, which is sufficient to prove "logs prompts/outputs
  transparently." A real HTTP-intercepting proxy is a later step, not needed
  to demo the value.
- No database — JSONL/JSON files only.
- No scheduling/cron/"continuous" background monitoring — the demo triggers
  a drift run manually via CLI command; "continuous" in production would just
  be this same command on a timer, which isn't itself part of the core value
  to prove.
- No auto-suggested prompt patch generation and no auto-fallback routing
  logic — both are real roadmap features but are separate from proving
  "we can detect and surface drift," which is the wedge. Stub these as a
  documented `TODO`/future-command placeholder only if trivial, otherwise omit
  entirely.
- No web UI/dashboard — the "report" is a Markdown/console table written to
  disk and printed to stdout.
- No real GPT-5.2/Gemini network calls required to validate the tool logic —
  optional and additive only.

## 3. File / directory layout

```
promptsentinel/
  README.md                     # how to run the demo, 60 seconds, no keys needed
  pyproject.toml                # package metadata; zero required deps
  requirements-optional.txt     # openai / anthropic SDKs, only if using live mode
  promptsentinel/
    __init__.py
    cli.py                      # argparse entrypoint: capture / baseline / run / report
    provider.py                 # Provider protocol + get_provider(name) factory
    providers/
      __init__.py
      mock_provider.py          # deterministic canned "before/after" responses
      openai_provider.py        # thin wrapper, only imported if --provider openai
      anthropic_provider.py     # thin wrapper, only imported if --provider anthropic
    capture.py                  # log_call(prompt, response, meta) -> appends JSONL
    baseline.py                 # pin current traffic/prompts as baseline.json
    diffing.py                  # compare(baseline_output, new_output) -> DriftResult
    report.py                   # render DriftResult list -> markdown + console table
    storage.py                  # tiny JSONL/JSON read-write helpers
  fixtures/
    sample_prompts.jsonl        # ~10-15 example prompts across a few "use cases"
    baseline_responses.jsonl    # canned "good" model outputs for those prompts
    drifted_responses.jsonl     # canned "post-update" outputs with injected drift
                                 # (one turns to refusal, one breaks JSON, one goes verbose/terse)
  .promptsentinel/              # runtime output dir, created on first run, gitignored
    traffic.jsonl                # captured prompt/response log
    baseline.json                # pinned baseline set
    reports/
      latest.md
  tests/
    test_diffing.py             # unit tests for each drift heuristic
    test_cli_e2e.py             # subprocess-runs the CLI end-to-end against fixtures
  .gitignore                    # ignores .promptsentinel/
```

## 4. Demo workflow (what the CLI proves, end to end)

1. `promptsentinel capture --provider mock --input fixtures/sample_prompts.jsonl`
   Simulates the proxy: runs each prompt through the mock provider (returning
   `baseline_responses.jsonl` content), logs prompt+response+timestamp+model-id
   to `.promptsentinel/traffic.jsonl`.
2. `promptsentinel baseline --pin`
   Snapshots current `traffic.jsonl` into `.promptsentinel/baseline.json` —
   this is "last known good."
3. Simulate a silent vendor model change: switch the mock provider's response
   set to `drifted_responses.jsonl` (flag: `--provider mock --drift-mode`).
4. `promptsentinel run --provider mock --drift-mode`
   Re-runs the *same* prompts from the baseline set, capturing new outputs.
5. `promptsentinel report`
   Diffs new outputs vs. baseline per-prompt across the heuristics (refusal
   flip, JSON-parseability flip, length/tone delta, text similarity below
   threshold), prints a table like:
   ```
   PROMPT_ID   STATUS     REASON
   p_001       OK         similarity 0.94
   p_002       REGRESSED  now refuses (was compliant)
   p_003       REGRESSED  JSON no longer parses
   p_004       OK         similarity 0.88
   ```
   and writes the same as `.promptsentinel/reports/latest.md`.
6. (Optional, only if user exports `OPENAI_API_KEY`) rerun the same flow with
   `--provider openai` against a real model to show the wrapper isn't
   mock-only — same commands, real data, no code changes.

## 5. Verification

- **Unit tests** (`tests/test_diffing.py`, run via `pytest`, no network/keys):
  - JSON that parses → still parses: no flag.
  - JSON that parses → now malformed: flags `json_parse_regression`.
  - Compliant answer → refusal phrase present: flags `refusal_regression`.
  - Near-identical text (similarity > threshold): no flag.
  - Divergent text (similarity below threshold): flags `content_drift`.
- **End-to-end test** (`tests/test_cli_e2e.py`): invokes the CLI as a
  subprocess through the full capture → baseline → drift-mode run → report
  sequence against the bundled fixtures, asserts the report contains the
  expected REGRESSED rows for the fixtures known to contain injected drift
  and OK for the ones that don't. This is the test that actually proves the
  core value end-to-end without any external dependency.
- **Manual run-through**: the six-command sequence in section 4, run by hand
  in a terminal with no env vars set, taking under a minute, ending in a
  human-readable drift report — this is the artifact to show anyone to prove
  the idea works.
- Run `pytest -q` and the manual sequence before calling the scaffold done.
