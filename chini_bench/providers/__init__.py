"""Provider registry. Each provider knows how to take a system+user prompt
and return a parsed CanvasState dict."""

from __future__ import annotations

from typing import Callable

from chini_bench.providers.anthropic_p import generate as _anthropic
from chini_bench.providers.ollama import generate as _ollama
from chini_bench.providers.openai_p import generate as _openai

GenerateFn = Callable[[str, str, str], dict]
# Signature: generate(system_prompt, user_prompt, model_id) -> CanvasState dict

PROVIDERS: dict[str, GenerateFn] = {
    "openai": _openai,
    "anthropic": _anthropic,
    "ollama": _ollama,
}


def get_provider(name: str) -> GenerateFn:
    if name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(sorted(PROVIDERS))}"
        )
    return PROVIDERS[name]
