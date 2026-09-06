"""Deterministic offline provider: serves canned responses from fixtures/.

Backs the entire no-key demo. `drift_mode=False` serves
`fixtures/baseline_responses.jsonl` ("before"); `drift_mode=True` serves
`fixtures/drifted_responses.jsonl` ("after" a simulated silent model update).
"""
from __future__ import annotations

from pathlib import Path

from .. import storage

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


class MockProvider:
    name = "mock"

    def __init__(self, *, drift_mode: bool = False):
        self.drift_mode = drift_mode
        filename = "drifted_responses.jsonl" if drift_mode else "baseline_responses.jsonl"
        self._responses = {row["id"]: row for row in storage.read_jsonl(FIXTURES_DIR / filename)}

    def respond(self, prompt_id: str, prompt: str) -> dict:
        row = self._responses.get(prompt_id)
        if row is None:
            raise KeyError(f"No canned mock response for prompt id {prompt_id!r}")
        return {"response": row["response"], "model": row.get("model", "mock-model")}
