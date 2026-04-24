"""Anthropic provider.

Uses the `anthropic` SDK if installed. The system prompt is passed as the
top-level `system` parameter rather than as a chat message.
"""

from __future__ import annotations

import os
from typing import Any

from chini_bench.providers.common import extract_json


def generate(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise RuntimeError(
            "Anthropic SDK not installed. Run: pip install anthropic"
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

    client = Anthropic(api_key=api_key)

    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0.2,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Anthropic returns a list of content blocks; we want the first text block.
    parts = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    raw = "".join(parts)
    return extract_json(raw)
