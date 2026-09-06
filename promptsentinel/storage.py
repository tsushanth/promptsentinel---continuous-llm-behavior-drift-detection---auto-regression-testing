"""Tiny JSONL/JSON read-write helpers, plus the default runtime file paths."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

DEFAULT_TRAFFIC_PATH = Path(".promptsentinel/traffic.jsonl")
DEFAULT_BASELINE_PATH = Path(".promptsentinel/baseline.json")
DEFAULT_REPORT_PATH = Path(".promptsentinel/reports/latest.md")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
