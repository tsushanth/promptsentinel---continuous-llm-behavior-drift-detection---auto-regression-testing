"""Thin wrapper around the OpenAI SDK. Only imported when --provider openai
is used, and only usable if the caller has already exported OPENAI_API_KEY
(BYO key, not a PromptSentinel account)."""
from __future__ import annotations

import os


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str = "gpt-4o-2024-08-06"):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Export it to use --provider openai, "
                "or use --provider mock for the offline demo."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The openai package is required for --provider openai. "
                "Install it with: pip install -r requirements-optional.txt"
            ) from exc
        self._client = OpenAI(api_key=api_key)
        self.model = model

    def respond(self, prompt_id: str, prompt: str) -> dict:
        completion = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "response": completion.choices[0].message.content,
            "model": completion.model,
        }
