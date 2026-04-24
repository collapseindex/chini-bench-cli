"""OpenRouter provider.

OpenRouter speaks the OpenAI Chat Completions API, so we reuse the `openai`
SDK with a custom base URL. Model ids look like `anthropic/claude-3.5-sonnet`,
`google/gemini-2.0-flash`, `meta-llama/llama-3.1-70b-instruct`, etc.
See https://openrouter.ai/models for the full list.
"""

from __future__ import annotations

import os
from typing import Any

from chini_bench.providers.common import extract_json

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def generate(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError(
            "OpenAI SDK not installed (used as the OpenRouter client). "
            "Run: pip install openai"
        ) from e

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set.")

    # OpenRouter rankings/attribution headers are optional but encouraged.
    default_headers = {
        "HTTP-Referer": os.environ.get(
            "OPENROUTER_REFERER", "https://chinilla.com/bench"
        ),
        "X-Title": os.environ.get("OPENROUTER_TITLE", "chini-bench"),
    }

    client = OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers=default_headers,
    )

    common_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    # Not every model on OpenRouter supports json_object; retry without on failure.
    try:
        resp = client.chat.completions.create(
            **common_kwargs,
            response_format={"type": "json_object"},
        )
    except Exception:
        resp = client.chat.completions.create(**common_kwargs)

    raw = resp.choices[0].message.content or ""
    return extract_json(raw)
