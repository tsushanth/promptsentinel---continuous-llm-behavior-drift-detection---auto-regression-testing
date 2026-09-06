"""Provider interface + factory.

Real provider SDKs (openai / anthropic) are imported lazily inside the
factory branches below, so importing this module never requires them.
"""
from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    """Anything that can turn a prompt into a model response."""

    name: str

    def respond(self, prompt_id: str, prompt: str) -> dict:
        """Return {"response": str, "model": str} for the given prompt."""
        ...


def get_provider(name: str, *, drift_mode: bool = False) -> Provider:
    if name == "mock":
        from .providers.mock_provider import MockProvider

        return MockProvider(drift_mode=drift_mode)
    if name == "openai":
        from .providers.openai_provider import OpenAIProvider

        return OpenAIProvider()
    if name == "anthropic":
        from .providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    raise ValueError(f"Unknown provider: {name!r} (expected mock, openai, or anthropic)")
