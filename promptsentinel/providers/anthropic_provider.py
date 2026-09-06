"""Thin wrapper around the Anthropic SDK. Only imported when
--provider anthropic is used, and only usable if the caller has already
exported ANTHROPIC_API_KEY (BYO key, not a PromptSentinel account)."""
from __future__ import annotations

import os


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-5"):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Export it to use --provider anthropic, "
                "or use --provider mock for the offline demo."
            )
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError(
                "The anthropic package is required for --provider anthropic. "
                "Install it with: pip install -r requirements-optional.txt"
            ) from exc
        self._client = Anthropic(api_key=api_key)
        self.model = model

    def respond(self, prompt_id: str, prompt: str) -> dict:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        return {"response": text, "model": message.model}
