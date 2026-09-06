"""Simulates the proxy: runs prompts through a provider and logs each
prompt/response exchange to the traffic log."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import storage
from .provider import Provider, get_provider
from .storage import DEFAULT_TRAFFIC_PATH


def log_call(traffic_path: Path, prompt_id: str, prompt: str, response: str,
             model: str, provider_name: str) -> dict:
    """Append one prompt/response exchange to the traffic log."""
    entry = {
        "id": prompt_id,
        "prompt": prompt,
        "response": response,
        "model": model,
        "provider": provider_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    storage.append_jsonl(traffic_path, entry)
    return entry


def _run_prompts(prompts: list[dict], provider: Provider, traffic_path: Path) -> list[dict]:
    traffic_path.parent.mkdir(parents=True, exist_ok=True)
    if traffic_path.exists():
        traffic_path.unlink()

    logged = []
    for row in prompts:
        result = provider.respond(row["id"], row["prompt"])
        entry = log_call(
            traffic_path, row["id"], row["prompt"],
            result["response"], result["model"], provider.name,
        )
        logged.append(entry)
    return logged


def capture(prompts_path: Path, provider_name: str, *, drift_mode: bool = False,
            traffic_path: Path = DEFAULT_TRAFFIC_PATH) -> list[dict]:
    """Run every prompt in `prompts_path` through a provider, logging results."""
    provider = get_provider(provider_name, drift_mode=drift_mode)
    prompts = list(storage.read_jsonl(prompts_path))
    return _run_prompts(prompts, provider, traffic_path)


def run_against_baseline(baseline_path: Path, provider_name: str, *, drift_mode: bool = False,
                          traffic_path: Path = DEFAULT_TRAFFIC_PATH) -> list[dict]:
    """Re-run the prompts pinned in the baseline through a (possibly drifted)
    provider, logging fresh outputs for comparison against that baseline."""
    provider = get_provider(provider_name, drift_mode=drift_mode)
    baseline = storage.read_json(baseline_path)
    prompts = [{"id": pid, "prompt": row["prompt"]} for pid, row in baseline.items()]
    return _run_prompts(prompts, provider, traffic_path)
