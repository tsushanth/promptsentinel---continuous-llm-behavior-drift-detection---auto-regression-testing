"""Heuristic drift detection: refusal flips, JSON breakage, length/tone
shifts, and general text divergence. Intentionally crude -- good enough to
demonstrate "we caught a regression," not a production NLP classifier."""
from __future__ import annotations

import difflib
import json
from dataclasses import dataclass

SIMILARITY_THRESHOLD = 0.6
LENGTH_RATIO_HIGH = 3.0
LENGTH_RATIO_LOW = 1 / 3.0

REFUSAL_PHRASES = (
    "i cannot",
    "i can't",
    "i'm sorry, but",
    "i am sorry, but",
    "i won't",
    "i will not",
    "as an ai",
    "i'm not able to",
    "i am not able to",
    "unable to assist",
    "cannot help with that",
    "can't help with that",
)


@dataclass
class DriftResult:
    prompt_id: str
    status: str  # "OK" or "REGRESSED"
    reason_code: str  # e.g. "refusal_regression", "ok"
    detail: str  # human-readable explanation
    similarity: float


def is_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in REFUSAL_PHRASES)


def is_json_parseable(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def compare(prompt_id: str, baseline_output: str, new_output: str) -> DriftResult:
    similarity = text_similarity(baseline_output, new_output)

    if is_refusal(new_output) and not is_refusal(baseline_output):
        return DriftResult(
            prompt_id, "REGRESSED", "refusal_regression",
            "now refuses (was compliant)", similarity,
        )

    if is_json_parseable(baseline_output) and not is_json_parseable(new_output):
        return DriftResult(
            prompt_id, "REGRESSED", "json_parse_regression",
            "JSON no longer parses", similarity,
        )

    length_ratio = len(new_output) / (len(baseline_output) or 1)
    if length_ratio >= LENGTH_RATIO_HIGH or length_ratio <= LENGTH_RATIO_LOW:
        return DriftResult(
            prompt_id, "REGRESSED", "length_drift",
            f"response length changed {length_ratio:.1f}x", similarity,
        )

    if similarity < SIMILARITY_THRESHOLD:
        return DriftResult(
            prompt_id, "REGRESSED", "content_drift",
            f"content diverged (similarity {similarity:.2f})", similarity,
        )

    return DriftResult(prompt_id, "OK", "ok", f"similarity {similarity:.2f}", similarity)
