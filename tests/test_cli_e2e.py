"""Subprocess-runs the CLI end-to-end against the bundled fixtures: this is
the test that proves the core value (capture -> baseline -> drift -> report)
without any external dependency."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FIXTURE = REPO_ROOT / "fixtures" / "sample_prompts.jsonl"


def run_cli(args, cwd):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "promptsentinel.cli", *args],
        cwd=cwd, env=env, capture_output=True, text=True,
    )


def parse_table(output: str) -> dict:
    statuses = {}
    for line in output.splitlines():
        parts = line.split(None, 2)
        if len(parts) >= 2 and parts[0].startswith("p_"):
            statuses[parts[0]] = parts[1]
    return statuses


def test_capture_baseline_drift_report_e2e(tmp_path):
    result = run_cli(["capture", "--provider", "mock", "--input", str(PROMPTS_FIXTURE)], tmp_path)
    assert result.returncode == 0, result.stderr

    result = run_cli(["baseline", "--pin"], tmp_path)
    assert result.returncode == 0, result.stderr

    result = run_cli(["run", "--provider", "mock", "--drift-mode"], tmp_path)
    assert result.returncode == 0, result.stderr

    result = run_cli(["report"], tmp_path)
    assert result.returncode == 1  # regressions were found
    statuses = parse_table(result.stdout)

    assert statuses["p_001"] == "OK"
    assert statuses["p_002"] == "REGRESSED"  # JSON breakage
    assert statuses["p_003"] == "REGRESSED"  # refusal
    assert statuses["p_008"] == "REGRESSED"  # verbosity blow-up
    assert statuses["p_010"] == "OK"

    report_path = tmp_path / ".promptsentinel" / "reports" / "latest.md"
    assert report_path.exists()
    assert "REGRESSED" in report_path.read_text()
