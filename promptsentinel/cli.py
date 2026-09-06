"""PromptSentinel CLI: capture / baseline / run / report."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import baseline as baseline_mod
from . import capture as capture_mod
from . import report as report_mod
from .storage import DEFAULT_BASELINE_PATH, DEFAULT_REPORT_PATH, DEFAULT_TRAFFIC_PATH

DEFAULT_PROMPTS_PATH = Path("fixtures/sample_prompts.jsonl")


def _add_provider_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider", default="mock", choices=["mock", "openai", "anthropic"],
        help="Which provider to run prompts through (default: mock).",
    )
    parser.add_argument(
        "--drift-mode", action="store_true",
        help="Mock provider only: serve the drifted response set to simulate "
             "a silent vendor model change.",
    )


def cmd_capture(args: argparse.Namespace) -> int:
    logged = capture_mod.capture(
        Path(args.input), args.provider, drift_mode=args.drift_mode,
        traffic_path=Path(args.traffic_path),
    )
    print(f"Captured {len(logged)} prompt/response pairs to {args.traffic_path}")
    return 0


def cmd_baseline(args: argparse.Namespace) -> int:
    if not args.pin:
        print("Nothing to do: pass --pin to snapshot current traffic as baseline.")
        return 1
    pinned = baseline_mod.pin_baseline(
        traffic_path=Path(args.traffic_path), baseline_path=Path(args.baseline_path),
    )
    print(f"Pinned {len(pinned)} prompts as baseline at {args.baseline_path}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    logged = capture_mod.run_against_baseline(
        Path(args.baseline_path), args.provider, drift_mode=args.drift_mode,
        traffic_path=Path(args.traffic_path),
    )
    print(f"Re-ran {len(logged)} baseline prompts, logged to {args.traffic_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    results = report_mod.diff_traffic_against_baseline(
        traffic_path=Path(args.traffic_path), baseline_path=Path(args.baseline_path),
    )
    report_mod.write_report(results, report_path=Path(args.report_path))
    print(report_mod.render_table(results))
    regressed = [r for r in results if r.status == "REGRESSED"]
    print(f"\n{len(regressed)}/{len(results)} prompts regressed. Full report: {args.report_path}")
    return 1 if regressed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptsentinel",
        description="Continuous LLM behavior-drift detection, running locally.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_capture = subparsers.add_parser(
        "capture", help="Run prompts through a provider and log the traffic.")
    p_capture.add_argument(
        "--input", default=str(DEFAULT_PROMPTS_PATH),
        help="JSONL file of prompts to run (default: fixtures/sample_prompts.jsonl).",
    )
    p_capture.add_argument("--traffic-path", default=str(DEFAULT_TRAFFIC_PATH))
    _add_provider_args(p_capture)
    p_capture.set_defaults(func=cmd_capture)

    p_baseline = subparsers.add_parser(
        "baseline", help="Pin current traffic as the 'last known good' baseline.")
    p_baseline.add_argument(
        "--pin", action="store_true",
        help="Snapshot .promptsentinel/traffic.jsonl into baseline.json.",
    )
    p_baseline.add_argument("--traffic-path", default=str(DEFAULT_TRAFFIC_PATH))
    p_baseline.add_argument("--baseline-path", default=str(DEFAULT_BASELINE_PATH))
    p_baseline.set_defaults(func=cmd_baseline)

    p_run = subparsers.add_parser(
        "run", help="Re-run the baseline prompts through a provider (e.g. after a model update).")
    p_run.add_argument("--baseline-path", default=str(DEFAULT_BASELINE_PATH))
    p_run.add_argument("--traffic-path", default=str(DEFAULT_TRAFFIC_PATH))
    _add_provider_args(p_run)
    p_run.set_defaults(func=cmd_run)

    p_report = subparsers.add_parser(
        "report", help="Diff current traffic against the baseline and print/write a drift report.")
    p_report.add_argument("--traffic-path", default=str(DEFAULT_TRAFFIC_PATH))
    p_report.add_argument("--baseline-path", default=str(DEFAULT_BASELINE_PATH))
    p_report.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
