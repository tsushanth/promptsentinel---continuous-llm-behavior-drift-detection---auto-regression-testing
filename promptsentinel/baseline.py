"""Pin the current traffic log as the baseline ('last known good')."""
from __future__ import annotations

from pathlib import Path

from . import storage
from .storage import DEFAULT_BASELINE_PATH, DEFAULT_TRAFFIC_PATH


def pin_baseline(traffic_path: Path = DEFAULT_TRAFFIC_PATH,
                  baseline_path: Path = DEFAULT_BASELINE_PATH) -> dict:
    entries = list(storage.read_jsonl(traffic_path))
    if not entries:
        raise RuntimeError(
            f"No traffic found at {traffic_path}. Run 'promptsentinel capture' first."
        )
    baseline = {entry["id"]: entry for entry in entries}
    storage.write_json(baseline_path, baseline)
    return baseline
