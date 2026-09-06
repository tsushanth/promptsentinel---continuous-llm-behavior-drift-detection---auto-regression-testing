# PromptSentinel

Continuous LLM behavior-drift detection & auto-regression testing.

Vendors silently change model behavior under a "frozen," dated model ID.
Output structure breaks, refusal rate creeps up, JSON stops parsing, tone
shifts — and you find out from user complaints, days later. PromptSentinel
captures real prompt/response traffic, pins it as a baseline ("last known
good"), and re-runs the same prompts later (against a live model, or after a
provider update) to flag exactly which prompts regressed and why.

This repo is a **local MVP scaffold**: no server, no accounts, no database.
Everything is flat JSON/JSONL files on disk, and the default demo runs fully
offline against a deterministic mock provider — no API key, no cost.

## What it proves

The core loop, end to end:

**capture real prompt/output pairs → pin a baseline → re-run the same
prompts later (or against a different model) → diff outputs → flag drift
(structure, refusal, tone, JSON-parseability) → show which prompts
regressed.**

Drift detection is intentionally crude (stdlib-only heuristics), not a
production NLP classifier — enough to demonstrate "we caught a regression":

- **Refusal regression** — a previously compliant answer now contains a
  refusal phrase ("I cannot...", "I'm sorry, but...").
- **JSON-parseability regression** — a response that used to parse as JSON
  no longer does.
- **Length/tone drift** — response length changes drastically (e.g. a
  one-liner becomes a five-paragraph essay).
- **Content drift** — text similarity between baseline and new output falls
  below a threshold.

## Quickstart (60 seconds, no API keys)

```bash
pip install -e .

# 1. Simulate the proxy: run the sample prompts through the mock provider
#    and log prompt/response pairs.
promptsentinel capture --provider mock --input fixtures/sample_prompts.jsonl

# 2. Pin the current traffic as "last known good."
promptsentinel baseline --pin

# 3. Simulate a silent vendor model update by re-running the SAME prompts
#    through the mock provider's "drifted" response set.
promptsentinel run --provider mock --drift-mode

# 4. Diff the new run against the baseline and print/write a drift report.
promptsentinel report
```

Expected output of `report`:

```
PROMPT_ID   STATUS     REASON
p_001       OK         similarity 1.00
p_002       REGRESSED  JSON no longer parses
p_003       REGRESSED  now refuses (was compliant)
...
p_008       REGRESSED  response length changed 5.3x
...

3/12 prompts regressed. Full report: .promptsentinel/reports/latest.md
```

The same report is written to `.promptsentinel/reports/latest.md`. All
runtime state lives under `.promptsentinel/` (gitignored) — delete it any
time to reset the demo.

If you don't want to `pip install -e .`, you can run the CLI directly with
`python -m promptsentinel.cli <command>` from the repo root.

## Using a real provider

Real provider calls are optional and additive — the tool works identically
with a live model, no code changes:

```bash
pip install -r requirements-optional.txt
export OPENAI_API_KEY=sk-...
promptsentinel capture --provider openai --input fixtures/sample_prompts.jsonl
promptsentinel baseline --pin
# ... wait for a provider update, or just re-run later ...
promptsentinel run --provider openai
promptsentinel report
```

`--provider anthropic` works the same way with `ANTHROPIC_API_KEY` set.
`--drift-mode` only applies to `--provider mock`.

## Layout

```
promptsentinel/
  cli.py                 argparse entrypoint: capture / baseline / run / report
  provider.py            Provider protocol + get_provider(name) factory
  providers/
    mock_provider.py     deterministic canned "before/after" responses
    openai_provider.py   thin wrapper, only imported for --provider openai
    anthropic_provider.py
  capture.py             logs each prompt/response exchange to traffic.jsonl
  baseline.py            pins current traffic as baseline.json
  diffing.py             compare(baseline_output, new_output) -> DriftResult
  report.py              renders DriftResult list -> markdown + console table
  storage.py             JSONL/JSON read-write helpers
fixtures/
  sample_prompts.jsonl       12 example prompts across a few use cases
  baseline_responses.jsonl   canned "good" model outputs
  drifted_responses.jsonl    canned "post-update" outputs with injected drift
.promptsentinel/          runtime output (created on first run, gitignored)
  traffic.jsonl
  baseline.json
  reports/latest.md
tests/
  test_diffing.py         unit tests for each drift heuristic
  test_cli_e2e.py         subprocess-runs the CLI end to end against fixtures
```

## Explicitly out of scope (this MVP)

No auth/accounts, no billing, no hosted proxy server, no database, no
scheduling/cron, no auto-suggested prompt patches, no auto-fallback routing,
no web UI. See `plan.md` for the full rationale — this scaffold proves the
detection loop; those are later, separate steps.

## Tests

```bash
pip install pytest
pytest -q
```

`test_diffing.py` covers each heuristic in isolation (JSON breakage, refusal
flip, near-identical text, divergent text, length blow-up). `test_cli_e2e.py`
runs the full `capture → baseline → run --drift-mode → report` sequence as a
subprocess against the bundled fixtures and asserts the expected
REGRESSED/OK rows — this is the test that proves the core value end to end
with no external dependency.
