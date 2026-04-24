"""OpenAI provider.

Uses the `openai` SDK if installed. JSON mode is requested when the model
supports it. Falls back to free-form completion otherwise.
"""

from __future__ import annotations

import os
from typing import Any

from chini_bench.providers.common import extract_json


def generate(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError(
            "OpenAI SDK not installed. Run: pip install openai"
        ) from e

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    client = OpenAI(api_key=api_key)

    # JSON mode is supported on most modern chat models; if the call rejects
    # the response_format, we retry without it.
    common_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    try:
        resp = client.chat.completions.create(
            **common_kwargs,
            response_format={"type": "json_object"},
        )
    except Exception:
        resp = client.chat.completions.create(**common_kwargs)

    raw = resp.choices[0].message.content or ""
    return extract_json(raw)
