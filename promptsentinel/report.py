"""Diff current traffic against the pinned baseline and render a report."""
from __future__ import annotations

from pathlib import Path

from . import storage
from .diffing import DriftResult, compare
from .storage import DEFAULT_BASELINE_PATH, DEFAULT_REPORT_PATH, DEFAULT_TRAFFIC_PATH


def diff_traffic_against_baseline(
    traffic_path: Path = DEFAULT_TRAFFIC_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
) -> list[DriftResult]:
    if not baseline_path.exists():
        raise RuntimeError(
            f"No baseline found at {baseline_path}. Run 'promptsentinel baseline --pin' first."
        )
    if not traffic_path.exists():
        raise RuntimeError(
            f"No traffic found at {traffic_path}. Run 'promptsentinel capture' or "
            "'promptsentinel run' first."
        )

    baseline = storage.read_json(baseline_path)
    current = {row["id"]: row for row in storage.read_jsonl(traffic_path)}

    results = []
    for prompt_id, base_row in sorted(baseline.items()):
        if prompt_id not in current:
            results.append(DriftResult(
                prompt_id, "REGRESSED", "missing",
                "prompt missing from current run", 0.0,
            ))
            continue
        results.append(compare(prompt_id, base_row["response"], current[prompt_id]["response"]))
    return results


def render_table(results: list[DriftResult]) -> str:
    header = f"{'PROMPT_ID':<12}{'STATUS':<11}REASON"
    lines = [header]
    for r in results:
        lines.append(f"{r.prompt_id:<12}{r.status:<11}{r.detail}")
    return "\n".join(lines)


def render_markdown(results: list[DriftResult]) -> str:
    regressed = [r for r in results if r.status == "REGRESSED"]
    lines = [
        "# PromptSentinel Drift Report",
        "",
        f"{len(results)} prompts checked, {len(regressed)} regressed.",
        "",
        "| Prompt ID | Status | Reason |",
        "| --- | --- | --- |",
    ]
    for r in results:
        lines.append(f"| {r.prompt_id} | {r.status} | {r.detail} |")
    return "\n".join(lines) + "\n"


def write_report(results: list[DriftResult], report_path: Path = DEFAULT_REPORT_PATH) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(results), encoding="utf-8")
